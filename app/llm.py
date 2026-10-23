"""Thin async client for any OpenAI-compatible chat-completions endpoint.

The provider is selected entirely through environment variables, so Groq,
OpenRouter, Together, a local vLLM server, etc. all work without code changes.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from .config import Settings

logger = logging.getLogger("chatbot.llm")

GROUNDED_SYSTEM_PROMPT = """You are a skilled backend engineer assistant for this website.
Answer the user's question using ONLY the supplied context.

Always structure the reply as:
Problem: <one line>
Likely cause: <one or two lines>
Fix steps:
1. ...
2. ...
Extra tips: <optional>

Rules:
- Every factual claim must come from the context. Never invent, guess, or add outside knowledge.
- If the context does not answer the question, say clearly that you could not find it in the available material and point to official docs.
- Ask a short follow-up question if the user's information is insufficient.
- Put commands/code in fenced code blocks.
- Reference source numbers when useful, e.g. (see [1]).
- Be concise and practical."""


class LLMError(RuntimeError):
    """Raised for any upstream failure. Carries a client-safe message."""

    def __init__(self, message: str, *, status_code: int = 502) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def build_messages(
    settings: Settings,
    history: list[dict[str, str]],
    user_message: str,
) -> list[dict[str, str]]:
    """Assemble the model prompt with bounded history.

    Only ``user``/``assistant`` roles are forwarded and the total context is
    truncated by character budget so a caller cannot force huge inputs.
    """
    allowed = {"user": 0, "assistant": 1}
    cleaned: list[tuple[int, str]] = []
    for item in history:
        role = (item.get("role") or "").lower()
        content = (item.get("content") or "").strip()
        if role not in allowed or not content:
            continue
        cleaned.append((allowed[role], content))

    cleaned = cleaned[-settings.max_history_messages:]

    messages: list[dict[str, str]] = [{"role": "system", "content": settings.system_prompt}]
    for _, content in cleaned:
        messages.append({"role": "user" if _ == 0 else "assistant", "content": content[: settings.max_input_chars]})
    messages.append({"role": "user", "content": user_message})

    return messages


async def _post_chat(
    settings: Settings,
    messages: list[dict[str, str]],
    *,
    client: httpx.AsyncClient | None = None,
) -> tuple[str, dict[str, Any]]:
    """Send a chat-completion request. Returns ``(reply_text, usage)``."""
    if not settings.llm_configured:
        raise LLMError("The assistant is not configured yet. Please contact the site owner.", status_code=503)

    payload = {
        "model": settings.llm_model,
        "messages": messages,
        "max_tokens": settings.max_output_tokens,
        "temperature": 0.7,
    }

    logger.info("LLM request: model=%s turns=%d", settings.llm_model, len(messages) - 1)

    owns_client = client is None
    if owns_client:
        client = httpx.AsyncClient(
            base_url=settings.llm_base_url,
            timeout=httpx.Timeout(settings.llm_timeout, connect=5.0),
            headers={"Authorization": f"Bearer {settings.llm_api_key}"},
        )

    try:
        response = await client.post("/chat/completions", json=payload)
    except httpx.TimeoutException:
        logger.warning("LLM request timed out after %ss", settings.llm_timeout)
        raise LLMError("The assistant took too long to respond. Please try again.", status_code=504)
    except httpx.HTTPError as exc:
        logger.warning("LLM transport error: %s", type(exc).__name__)
        raise LLMError("Could not reach the AI service. Please try again shortly.", status_code=502)
    finally:
        if owns_client:
            await client.aclose()

    if response.status_code in (401, 403):
        logger.warning("LLM rejected credentials (HTTP %s)", response.status_code)
        raise LLMError("The assistant is misconfigured. Please contact the site owner.", status_code=503)
    if response.status_code == 429:
        logger.warning("LLM rate limit hit (HTTP 429)")
        raise LLMError("The assistant is busy right now. Please try again in a moment.", status_code=429)
    if response.status_code >= 400:
        logger.warning("LLM returned HTTP %s", response.status_code)
        raise LLMError("The AI service returned an error. Please try again.", status_code=502)

    try:
        data = response.json()
        reply = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {}) if isinstance(data.get("usage", {}), dict) else {}
    except (KeyError, IndexError, TypeError, ValueError):
        logger.warning("LLM returned an unexpected payload shape")
        raise LLMError("The AI service returned an unexpected response.", status_code=502)

    return (reply or "").strip(), usage


async def complete_chat(
    settings: Settings,
    history: list[dict[str, str]],
    user_message: str,
    *,
    client: httpx.AsyncClient | None = None,
) -> tuple[str, dict[str, Any]]:
    """Plain conversation mode (no knowledge base)."""
    messages = build_messages(settings, history, user_message)
    return await _post_chat(settings, messages, client=client)


async def generate_grounded_answer(
    settings: Settings,
    context: str,
    question: str,
    history: list[dict[str, str]],
    *,
    client: httpx.AsyncClient | None = None,
) -> tuple[str, dict[str, Any]]:
    """Answer strictly from the retrieved context (RAG mode)."""
    allowed = {"user": 0, "assistant": 1}
    cleaned: list[tuple[int, str]] = []
    for item in history:
        role = (item.get("role") or "").lower()
        content = (item.get("content") or "").strip()
        if role in allowed and content:
            cleaned.append((allowed[role], content))
    cleaned = cleaned[-settings.max_history_messages:]

    messages: list[dict[str, str]] = [
        {"role": "system", "content": GROUNDED_SYSTEM_PROMPT},
    ]
    for _, content in cleaned:
        messages.append({"role": "user" if _ == 0 else "assistant", "content": content[: settings.max_input_chars]})
    messages.append(
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {question}",
        }
    )

    return await _post_chat(settings, messages, client=client)
