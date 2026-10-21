"""Retrieval: turn a question into the most relevant knowledge-base chunks.

This is the single seam that makes the system swappable. The rest of the app
only ever calls :func:`retrieve`, so replacing vector search with hybrid
BM25+vector later means changing this file and nothing else.
"""
from __future__ import annotations

import logging
from typing import Any

from ..config import Settings
from ..llm import LLMError
from . import embed
from .chunk import Chunk, truncate_for_prompt
from .store import QdrantStore, RetrievedChunk

logger = logging.getLogger("chatbot.kb.retrieve")

# Query embeddings are deterministic and not sensitive, so cache them to stay
# well inside Jina's free-tier rate limit.
_CACHE_LIMIT = 512
_query_cache: dict[str, list[float]] = {}


async def retrieve(
    query: str,
    settings: Settings,
    *,
    top_k: int | None = None,
    min_score: float | None = None,
    store: QdrantStore | None = None,
) -> list[RetrievedChunk]:
    """Return the chunks most relevant to `query`, best first.

    Returns an empty list when nothing clears the similarity threshold — the
    caller is expected to say "I don't know" rather than guess.
    """
    top_k = top_k if top_k is not None else settings.kb_top_k
    min_score = min_score if min_score is not None else settings.kb_min_score

    store = store or QdrantStore(settings)

    vector = _query_cache.get(query)
    if vector is None:
        vector = await embed.embed_query(settings, query)
        if len(_query_cache) >= _CACHE_LIMIT:
            _query_cache.clear()
        _query_cache[query] = vector
    else:
        logger.debug("Embedding cache hit for query")

    hits = store.search(vector, top_k=top_k, min_score=min_score)

    logger.info(
        "Retrieved %d chunks for query (top score %s, min_score %.2f)",
        len(hits),
        hits[0].score if hits else "none",
        min_score,
    )
    return hits


def build_context(chunks: list[RetrievedChunk], max_chars: int) -> str:
    """Render retrieved chunks into the prompt's context block.

    Each chunk is labelled with its citation so the model can quote sources.
    """
    kept = truncate_for_prompt(chunks, max_chars)

    blocks: list[str] = []
    for i, chunk in enumerate(kept, start=1):
        blocks.append(f"[{i}] Source: {chunk.citation()}\n{chunk.text}")

    return "\n\n".join(blocks)


def citations_from(chunks: list[RetrievedChunk]) -> list[dict[str, Any]]:
    """Unique source citations, best-scoring first."""
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for chunk in chunks:
        key = chunk.citation()
        if key in seen:
            continue
        seen.add(key)
        out.append({"source": chunk.source, "section": chunk.section, "score": chunk.score})
    return out


def raise_if_unavailable(settings: Settings) -> None:
    """Fail fast with a client-safe message if retrieval cannot run."""
    if not settings.embeddings_configured:
        raise LLMError("The knowledge base is not configured. Please contact the site owner.", status_code=503)
    if not settings.qdrant_configured:
        raise LLMError("The knowledge base is unavailable. Please contact the site owner.", status_code=503)
