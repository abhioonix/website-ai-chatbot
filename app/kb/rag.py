"""End-to-end RAG answering: retrieve -> ground -> answer -> cite.

This is the layer the API calls. It guarantees two properties:

  * If nothing relevant is retrieved, the user gets an honest "not found" answer
    with no sources — the model is never asked to improvise.
  * If an answer is produced, every chunk used is returned as a citation.
"""
from __future__ import annotations

import logging
from typing import Any

from .. import llm
from ..config import Settings
from ..llm import LLMError
from .retrieve import build_context, citations_from, retrieve

logger = logging.getLogger("chatbot.kb.rag")

NOT_FOUND_REPLY = (
    "I couldn't find that in the material available to me. "
    "I only answer from the knowledge base, so I'd rather not guess. "
    "Try rephrasing with more specific terms, or ask about something else."
)


async def answer_from_knowledge_base(
    question: str,
    history: list[dict[str, str]],
    settings: Settings,
) -> dict[str, Any]:
    """Answer a question strictly from the knowledge base.

    Returns ``{"reply", "sources", "grounded", "matched"}``.
    """
    chunks = await retrieve(question, settings)

    if not chunks:
        # Nothing relevant in the KB — fall back to a generic LLM answer
        # instead of refusing, so the chatbot stays helpful.
        logger.info("No relevant chunks for question — falling back to generic LLM answer")
        reply, usage = await llm.complete_chat(settings, history, question)
        return {
            "reply": reply,
            "sources": [],
            "grounded": False,
            "matched": 0,
            "usage": usage,
        }

    context = build_context(chunks, settings.kb_max_context_chars)
    sources = citations_from(chunks)

    try:
        reply, usage = await llm.generate_grounded_answer(settings, context, question, history)
    except LLMError:
        # Retrieval worked but generation failed — surface the safe error.
        raise

    return {
        "reply": reply,
        "sources": sources,
        "grounded": True,
        "matched": len(chunks),
        "usage": usage,
    }
