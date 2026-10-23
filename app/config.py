"""Configuration loaded from environment variables.

Secrets are read only from the process environment (or a local `.env` file
during development). Nothing here is written to the repository.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path


def _load_dotenv() -> None:
    """Minimal .env loader for local development.

    Deployment platforms inject environment variables directly, so this is a
    convenience only. Real environment values always win.
    """
    path = Path(__file__).resolve().parent.parent / ".env"
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_dotenv()


class Settings:
    """Typed view over the environment."""

    def __init__(self) -> None:
        # --- LLM provider (OpenAI-compatible chat completions) ------------
        self.llm_api_key: str = os.getenv("LLM_API_KEY", "").strip()
        self.llm_base_url: str = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1").strip().rstrip("/")
        self.llm_model: str = os.getenv("LLM_MODEL", "openai/gpt-oss-20b").strip()
        self.llm_timeout: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))

        # --- Embeddings (Jina AI, free tier, no card) ---------------------
        self.jina_api_key: str = os.getenv("JINA_API_KEY", "").strip()
        self.jina_base_url: str = os.getenv("JINA_BASE_URL", "https://api.jina.ai/v1").strip().rstrip("/")
        self.jina_embed_model: str = os.getenv("JINA_EMBED_MODEL", "jina-embeddings-v3").strip()
        self.jina_embed_dims: int = int(os.getenv("JINA_EMBED_DIMS", "1024"))
        self.jina_task_passage: str = os.getenv("JINA_TASK_PASSAGE", "retrieval.passage")
        self.jina_task_query: str = os.getenv("JINA_TASK_QUERY", "retrieval.query")

        # --- Vector store (Qdrant Cloud free tier, no card) ---------------
        self.qdrant_url: str = os.getenv("QDRANT_URL", "").strip()
        self.qdrant_api_key: str = os.getenv("QDRANT_API_KEY", "").strip()
        self.qdrant_collection: str = os.getenv("QDRANT_COLLECTION", "website_kb").strip()
        self.qdrant_local: bool = os.getenv("QDRANT_LOCAL", "").strip().lower() in {"1", "true", "yes"}

        # --- Knowledge base behaviour -------------------------------------
        self.kb_enabled: bool = os.getenv("KB_ENABLED", "false").strip().lower() in {"1", "true", "yes"}
        self.kb_source_dir: str = os.getenv("KB_SOURCE_DIR", "knowledge_base").strip()
        self.kb_chunk_size: int = int(os.getenv("KB_CHUNK_SIZE", "600"))
        self.kb_chunk_overlap: int = int(os.getenv("KB_CHUNK_OVERLAP", "100"))
        self.kb_top_k: int = int(os.getenv("KB_TOP_K", "4"))
        # Cosine similarity is in [-1, 1]; 0.5 is a reasonable floor.
        self.kb_min_score: float = float(os.getenv("KB_MIN_SCORE", "0.5"))
        self.kb_max_context_chars: int = int(os.getenv("KB_MAX_CONTEXT_CHARS", "4000"))

        # --- Widget / security --------------------------------------------
        origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
        self.allowed_origins: list[str] = [o.strip() for o in origins.split(",") if o.strip()]
        self.allow_any_origin: bool = "*" in self.allowed_origins

        self.rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "20"))
        self.max_body_bytes: int = int(os.getenv("MAX_BODY_BYTES", "8192"))
        self.max_input_chars: int = int(os.getenv("MAX_INPUT_CHARS", "2000"))
        self.max_history_messages: int = int(os.getenv("MAX_HISTORY_MESSAGES", "10"))
        self.max_output_tokens: int = int(os.getenv("MAX_OUTPUT_TOKENS", "512"))

        self.host: str = os.getenv("HOST", "0.0.0.0")
        self.port: int = int(os.getenv("PORT", "8000"))

        self.system_prompt: str = (
            "You are a skilled backend engineer assistant for website visitors. "
            "Answer backend questions (APIs, databases, servers, FastAPI, Node.js, Python, ops) clearly and practically. "
            "Structure replies as: Problem, Likely cause, Fix steps, Extra tips. "
            "Ask a follow-up if info is insufficient. Warn not to paste secrets. Keep replies short."
        )

    # ------------------------------------------------------------------
    @property
    def llm_configured(self) -> bool:
        return bool(self.llm_api_key)

    @property
    def embeddings_configured(self) -> bool:
        return bool(self.jina_api_key)

    @property
    def qdrant_configured(self) -> bool:
        """True for cloud mode or explicitly-enabled local mode."""
        return bool(self.qdrant_url and self.qdrant_api_key) or self.qdrant_local

    @property
    def rag_ready(self) -> bool:
        """True when the whole retrieval pipeline can run."""
        return self.kb_enabled and self.embeddings_configured and self.qdrant_configured


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
