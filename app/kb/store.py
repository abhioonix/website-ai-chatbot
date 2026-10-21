"""Qdrant vector store — the retrieval half of RAG.

Runs against Qdrant Cloud (free tier, no card) when `QDRANT_URL` and
`QDRANT_API_KEY` are set, or in local in-memory mode when `QDRANT_LOCAL=1`
(handy for tests and offline development).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from ..config import Settings
from ..llm import LLMError
from .chunk import Chunk

logger = logging.getLogger("chatbot.kb.store")

# In Qdrant's `:memory:` mode every client gets its own private database, so
# separate store instances would not see each other's points. Share one local
# client per collection so the whole app (and the test-suite) sees one index.
_LOCAL_CLIENTS: dict[str, Any] = {}


def _shared_local_client(collection_name: str):  # noqa: ANN202
    if collection_name not in _LOCAL_CLIENTS:
        from qdrant_client import QdrantClient

        _LOCAL_CLIENTS[collection_name] = QdrantClient(":memory:", check_compatibility=False)
    return _LOCAL_CLIENTS[collection_name]


def reset_local_clients() -> None:
    """Drop all shared local clients — used by tests for isolation."""
    _LOCAL_CLIENTS.clear()


@dataclass
class RetrievedChunk:
    """A chunk returned from the vector store, with its similarity score."""

    id: str
    text: str
    source: str
    section: str | None
    score: float

    def citation(self) -> str:
        return f"{self.source} — {self.section}" if self.section else self.source


class QdrantStore:
    """Thin async-friendly wrapper around the Qdrant client."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client: Any = None

    # ------------------------------------------------------------------
    def _get_client(self):  # noqa: ANN202
        if self._client is None:
            try:
                from qdrant_client import QdrantClient
            except ImportError as exc:
                raise LLMError(
                    "Vector search is unavailable (qdrant-client not installed).",
                    status_code=503,
                ) from exc

            if self.settings.qdrant_local:
                self._client = _shared_local_client(self.settings.qdrant_collection)
                logger.info("Using shared local in-memory Qdrant")
            else:
                self._client = QdrantClient(
                    url=self.settings.qdrant_url,
                    api_key=self.settings.qdrant_api_key,
                    timeout=30,
                )
                logger.info("Connected to Qdrant Cloud at %s", self.settings.qdrant_url)
        return self._client

    # ------------------------------------------------------------------
    def ensure_collection(self, vector_size: int) -> None:
        from qdrant_client import models

        client = self._get_client()
        name = self.settings.qdrant_collection
        try:
            existing = client.get_collection(name)
            if existing.config.params.vectors.size != vector_size:
                logger.warning(
                    "Collection %s has %d dims, expected %d — recreating",
                    name,
                    existing.config.params.vectors.size,
                    vector_size,
                )
                client.delete_collection(name)
                existing = None
        except Exception:  # noqa: BLE001
            existing = None

        if existing is None:
            client.create_collection(
                collection_name=name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE,
                ),
            )
            logger.info("Created collection %s (%d dims)", name, vector_size)

    # ------------------------------------------------------------------
    def upsert(self, chunks: list[Chunk], vectors: list[list[float]]) -> int:
        from qdrant_client import models

        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must be the same length")

        client = self._get_client()
        points = [
            models.PointStruct(
                id=chunk.id,
                vector=vector,
                payload={
                    "text": chunk.text,
                    "source": chunk.source,
                    "section": chunk.section,
                    "order": chunk.order,
                },
            )
            for chunk, vector in zip(chunks, vectors)
        ]
        client.upsert(collection_name=self.settings.qdrant_collection, points=points)
        return len(points)

    # ------------------------------------------------------------------
    def search(self, vector: list[float], top_k: int, min_score: float) -> list[RetrievedChunk]:
        client = self._get_client()
        try:
            hits = client.query_points(
                collection_name=self.settings.qdrant_collection,
                query=vector,
                limit=max(1, top_k),
            ).points
        except Exception as exc:  # noqa: BLE001
            logger.warning("Vector search failed: %s", exc)
            raise LLMError("The search service returned an error. Please try again.", status_code=502)

        results: list[RetrievedChunk] = []
        for hit in hits:
            payload = hit.payload or {}
            score = float(hit.score)
            if score < min_score:
                continue
            results.append(
                RetrievedChunk(
                    id=str(hit.id),
                    text=str(payload.get("text", "")),
                    source=str(payload.get("source", "unknown")),
                    section=payload.get("section"),
                    score=round(score, 4),
                )
            )
        return results

    # ------------------------------------------------------------------
    def count(self) -> int:
        client = self._get_client()
        try:
            return int(client.get_collection(self.settings.qdrant_collection).points_count or 0)
        except Exception:  # noqa: BLE001
            return 0

    def clear(self) -> None:
        """Delete the collection's contents — used when rebuilding the index.

        The shared local client is kept alive so other store instances still
        see the recreated collection.
        """
        client = self._get_client()
        name = self.settings.qdrant_collection
        try:
            client.delete_collection(name)
        except Exception:  # noqa: BLE001
            pass
