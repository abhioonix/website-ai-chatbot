"""Rebuild the knowledge-base vector index.

Run this after adding or editing files in the knowledge_base/ directory:

    python3 -m scripts.rebuild_index

It loads every .md/.txt/.json/.pdf file, chunks it, embeds each chunk with
Jina, and upserts the vectors into Qdrant.
"""
from __future__ import annotations

import asyncio
import json
import sys

from app.config import get_settings
from app.kb.index import rebuild_index


async def main() -> int:
    settings = get_settings()
    if not settings.embeddings_configured:
        print("JINA_API_KEY is not set — cannot embed. Add it to your environment.", file=sys.stderr)
        return 2
    if not settings.qdrant_configured:
        print("QDRANT_URL / QDRANT_API_KEY are not set — cannot store vectors.", file=sys.stderr)
        return 2

    try:
        stats = await rebuild_index(settings)
    except Exception as exc:  # noqa: BLE001
        print(f"Rebuild failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
