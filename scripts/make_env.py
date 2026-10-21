"""Build a local .env for development from the key stored in Intern_15_PJT.

The .env file is git-ignored. This script never prints the key.

RAG variables are written as placeholders. Fill in the real Jina and Qdrant
values from the environment before running `python3 -m scripts.rebuild_index`.

Run:  python3 scripts/make_env.py
"""

from __future__ import annotations

import re
from pathlib import Path

KEY_FILE = Path("/home/weirdvella/Intern_15_PJT/AAAAAapi.txt")
TARGET = Path(__file__).resolve().parent.parent / ".env"

CONTENT = """# Generated locally by scripts/make_env.py — git-ignored, do not commit.
# Fill in JINA_* / QDRANT_* below before rebuilding the knowledge-base index.

# --- LLM provider ---------------------------------------------------
LLM_API_KEY={key}
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=openai/gpt-oss-20b

# --- Embeddings (Jina AI, free tier, no card) ------------------------
JINA_API_KEY=
JINA_BASE_URL=https://api.jina.ai/v1
JINA_EMBED_MODEL=jina-embeddings-v3
JINA_EMBED_DIMS=1024

# --- Vector store (Qdrant Cloud free tier, no card) ------------------
QDRANT_URL=
QDRANT_API_KEY=
QDRANT_COLLECTION=website_kb
QDRANT_LOCAL=0

# --- Knowledge base --------------------------------------------------
# Master switch. Keep true so /api/chat answers from the KB with citations.
KB_ENABLED=true
KB_SOURCE_DIR=knowledge_base
KB_MIN_SCORE=0.5
KB_ADMIN_TOKEN=

# --- Widget / security ----------------------------------------------
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174
RATE_LIMIT_PER_MINUTE=20
MAX_BODY_BYTES=8192
MAX_INPUT_CHARS=2000
MAX_HISTORY_MESSAGES=10
MAX_OUTPUT_TOKENS=512

# --- Server ----------------------------------------------------------
HOST=0.0.0.0
PORT=8000
"""


def main() -> None:
    if not KEY_FILE.is_file():
        raise SystemExit(f"key file not found: {KEY_FILE}")

    match = re.search(r"gsk_[A-Za-z0-9]{20,}", KEY_FILE.read_text(errors="ignore"))
    if not match:
        raise SystemExit(f"no gsk_ key found in {KEY_FILE}")

    TARGET.write_text(CONTENT.format(key=match.group(0)), encoding="utf-8")
    print(f"wrote {TARGET} (llm key length {len(match.group(0))})")


if __name__ == "__main__":
    main()
