"""Jina AI embedding client (free tier — no credit card required).

Speaks the OpenAI-style `/embeddings` shape so swapping providers later is a
one-line change. Uses Jina's asymmetric `task` parameter: documents are embedded
as `retrieval.passage` and queries as `retrieval.query`, which measurably
improves retrieval quality for question-answering.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from ..config import Settings
from ..llm import LLMError

logger = logging.getLogger("chatbot.kb.embed")


async def embed_texts(
    settings: Settings,
    texts: list[str],
    *,
    task: str,
    client: httpx.AsyncClient | None = None,
) -> list[list[float]]:
    """Embed a batch of texts. Returns one vector per input, in order.

    Raises :class:`LLMError` with a client-safe message on any failure.
    """
    if not settings.jina_api_key:
        raise LLMError("Embeddings are not configured. Please contact the site owner.", status_code=503)
    if not texts:
        return []

    payload: dict[str, Any] = {
        "model": settings.jina_embed_model,
        "task": task,
        "dimensions": settings.jina_embed_dims,
        "input": texts,
    }

    owns_client = client is None
    if owns_client:
        client = httpx.AsyncClient(
            base_url=settings.jina_base_url,
            timeout=httpx.Timeout(30.0, connect=5.0),
            headers={
                "Authorization": f"Bearer {settings.jina_api_key}",
                "Content-Type": "application/json",
            },
        )

    logger.info("Embedding %d texts (task=%s, dims=%d)", len(texts), task, settings.jina_embed_dims)

    try:
        response = await client.post("/embeddings", json=payload)
    except httpx.TimeoutException:
        raise LLMError("The search service timed out. Please try again.", status_code=504)
    except httpx.HTTPError as exc:
        logger.warning("Embedding transport error: %s", type(exc).__name__)
        raise LLMError("Could not reach the search service. Please try again shortly.", status_code=502)
    finally:
        if owns_client:
            await client.aclose()

    if response.status_code in (401, 403):
        raise LLMError("The search service rejected its credentials. Please contact the site owner.", status_code=503)
    if response.status_code == 429:
        raise LLMError("The search service is busy. Please try again in a moment.", status_code=429)
    if response.status_code >= 400:
        logger.warning("Embedding API returned HTTP %s", response.status_code)
        raise LLMError("The search service returned an error.", status_code=502)

    try:
        data = response.json()
        items = data["data"]
        vectors = [item["embedding"] for item in items]
    except (KeyError, IndexError, TypeError, ValueError):
        raise LLMError("The search service returned an unexpected response.", status_code=502)

    # Jina may reorder; honour the index field when present.
    if items and "index" in items[0]:
        vectors = [None] * len(items)  # type: ignore[list-item]
        for item in items:
            vectors[item["index"]] = item["embedding"]  # type: ignore[index]

    if len(vectors) != len(texts):
        raise LLMError("The search service returned the wrong number of vectors.", status_code=502)

    return [v for v in vectors if v is not None]


async def embed_query(settings: Settings, query: str) -> list[float]:
    """Embed a single user query using the query-specific task."""
    vectors = await embed_texts(settings, [query], task=settings.jina_task_query)
    return vectors[0]
