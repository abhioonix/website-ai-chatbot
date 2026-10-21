"""Index building: load -> chunk -> embed -> upsert.

Run on a schedule or whenever the knowledge source changes. Chunk ids are
content-hashes, so re-running is idempotent — unchanged text is simply
overwritten rather than duplicated.
"""
from __future__ import annotations

import logging
from typing import Any

from ..config import Settings
from ..llm import LLMError
from . import embed
from .chunk import chunk_documents
from .load import load_documents
from .store import QdrantStore

logger = logging.getLogger("chatbot.kb.index")

BATCH_SIZE = 32


async def rebuild_index(settings: Settings, *, clear: bool = True) -> dict[str, Any]:
    """Build or refresh the whole vector index. Returns index statistics."""
    if not settings.embeddings_configured:
        raise LLMError("Embeddings are not configured.", status_code=503)
    if not settings.qdrant_configured:
        raise LLMError("Vector store is not configured.", status_code=503)

    documents = load_documents(settings.kb_source_dir)
    if not documents:
        raise LLMError(
            f"No documents found in '{settings.kb_source_dir}'. Add .md, .txt, .json or .pdf files.",
            status_code=500,
        )

    chunks = chunk_documents(
        documents,
        chunk_size=settings.kb_chunk_size,
        overlap=settings.kb_chunk_overlap,
    )
    if not chunks:
        raise LLMError("Documents produced no usable chunks.", status_code=500)

    store = QdrantStore(settings)
    if clear:
        store.clear()
    store.ensure_collection(vector_size=settings.jina_embed_dims)

    embedded = 0
    for start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[start : start + BATCH_SIZE]
        vectors = await embed.embed_texts(
            settings,
            [chunk.text for chunk in batch],
            task=settings.jina_task_passage,
        )
        store.upsert(batch, vectors)
        embedded += len(batch)
        logger.info("Indexed %d/%d chunks", embedded, len(chunks))

    total = store.count()
    logger.info(
        "Index rebuilt: %d documents -> %d chunks, %d stored in collection '%s'",
        len(documents),
        len(chunks),
        total,
        settings.qdrant_collection,
    )

    return {
        "documents": len(documents),
        "chunks": len(chunks),
        "stored": total,
        "collection": settings.qdrant_collection,
        "dimensions": settings.jina_embed_dims,
    }


def index_status(settings: Settings) -> dict[str, Any]:
    """Report whether the index exists and how full it is — no embedding calls."""
    store = QdrantStore(settings)
    try:
        count = store.count()
    except Exception:  # noqa: BLE001
        count = 0
    return {
        "enabled": settings.rag_ready,
        "embeddings_configured": settings.embeddings_configured,
        "vector_store_configured": settings.qdrant_configured,
        "collection": settings.qdrant_collection,
        "chunks_stored": count,
        "source_dir": settings.kb_source_dir,
    }
