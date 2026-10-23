"""website-ai-chatbot — a small, standalone chat widget backend.

Endpoints
    GET  /health      liveness/readiness probe (+ knowledge-base status)
    GET  /widget.js   the embeddable widget script (same-origin by default)
    GET  /kb/status   is the knowledge base indexed and ready?
    POST /kb/rebuild  rebuild the vector index (needs KB_ADMIN_TOKEN)
    POST /api/chat    send a message, receive an assistant reply

When the knowledge base is enabled and indexed, `/api/chat` answers strictly
from it (RAG mode) and returns citations. Otherwise it falls back to a plain
conversation with the LLM.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from . import llm
from .config import Settings, get_settings
from .llm import LLMError
from .models import (
    ChatRequest,
    ChatResponse,
    ErrorResponse,
    KBStatusResponse,
    RebuildResponse,
    SourceCitation,
)
from .security import RateLimitExceeded, RateLimiter, client_ip

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("chatbot")

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
WIDGET_PATH = STATIC_DIR / "widget.js"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    limiter = RateLimiter(settings.rate_limit_per_minute)

    app = FastAPI(
        title="website-ai-chatbot",
        version="2.0.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    if settings.allow_any_origin:
        logger.warning("ALLOWED_ORIGINS contains '*' — CORS is wide open. Fine for a prototype, tighten for production.")
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=False,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["content-type"],
        )
    else:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.allowed_origins,
            allow_credentials=False,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["content-type", "x-kb-admin-token"],
        )

    @app.middleware("http")
    async def limit_body_size(request: Request, call_next):  # noqa: ANN001, ANN202
        content_length = request.headers.get("content-length")
        if content_length and content_length.isdigit() and int(content_length) > settings.max_body_bytes:
            return JSONResponse({"error": "Request too large."}, status_code=413)
        return await call_next(request)

    def enforce_rate_limit(request: Request) -> None:  # noqa: ANN001
        allowed, _meta = limiter.check(client_ip(request))
        if not allowed:
            raise RateLimitExceeded("Too many requests. Please slow down.")

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:  # noqa: ANN001, ARG002
        return JSONResponse({"error": str(exc)}, status_code=429, headers={"Retry-After": "30"})

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:  # noqa: ANN001, ARG002
        """Never leak tracebacks or internal details to the client."""
        logger.exception("Unhandled error while serving %s", request.url.path)
        return JSONResponse({"error": "Something went wrong on our side. Please try again."}, status_code=500)

    # ------------------------------------------------------------------
    # Routes
    # ------------------------------------------------------------------
    @app.get("/health", tags=["ops"])
    async def health() -> dict:
        from .kb.index import index_status

        return {
            "status": "ok",
            "llm_configured": settings.llm_configured,
            "model": settings.llm_model,
            "knowledge_base": index_status(settings),
        }

    @app.get("/widget.js", tags=["widget"])
    async def widget_js() -> FileResponse:
        if not WIDGET_PATH.is_file():
            return JSONResponse({"error": "Widget not found."}, status_code=404)
        return FileResponse(
            WIDGET_PATH,
            media_type="application/javascript; charset=utf-8",
            headers={"Cache-Control": "public, max-age=300"},
        )

    # ------------------------------------------------------------------
    # Knowledge base management
    # ------------------------------------------------------------------
    @app.get("/kb/status", response_model=KBStatusResponse, tags=["knowledge-base"])
    async def kb_status() -> KBStatusResponse:
        from .kb.index import index_status

        return KBStatusResponse(**index_status(settings))

    @app.post("/kb/rebuild", response_model=RebuildResponse, tags=["knowledge-base"])
    async def kb_rebuild(request: Request) -> Response:
        """Rebuild the vector index. Requires KB_ADMIN_TOKEN when one is set."""
        enforce_rate_limit(request)

        token = os.getenv("KB_ADMIN_TOKEN", "").strip()
        if token:
            provided = request.headers.get("x-kb-admin-token", "")
            if provided != token:
                return JSONResponse({"error": "Not allowed."}, status_code=403)

        from .kb.index import rebuild_index

        try:
            stats = await rebuild_index(settings)
        except LLMError as exc:
            return JSONResponse({"error": exc.message}, status_code=exc.status_code)

        return RebuildResponse(ok=True, **stats, message="Index rebuilt.")

    # ------------------------------------------------------------------
    # Chat
    # ------------------------------------------------------------------
    @app.post(
        "/api/chat",
        response_model=ChatResponse,
        responses={
            400: {"model": ErrorResponse},
            413: {"model": ErrorResponse},
            429: {"model": ErrorResponse},
            502: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
        tags=["chat"],
    )
    async def chat(payload: ChatRequest, request: Request) -> Response:  # noqa: ANN001
        enforce_rate_limit(request)

        message = payload.message.strip()
        if not message:
            return JSONResponse({"error": "Message cannot be empty."}, status_code=400)
        if len(message) > settings.max_input_chars:
            return JSONResponse(
                {"error": f"Message is too long (max {settings.max_input_chars} characters)."},
                status_code=400,
            )

        history = [m.model_dump() for m in payload.history]

        # RAG mode: answer strictly from the knowledge base.
        if settings.rag_ready:
            from .kb.rag import answer_from_knowledge_base

            try:
                result = await answer_from_knowledge_base(message, history, settings)
            except LLMError as exc:
                logger.warning("RAG chat failed: %s", exc.message)
                return JSONResponse({"error": exc.message}, status_code=exc.status_code)

            return ChatResponse(
                reply=result["reply"],
                model=settings.llm_model,
                grounded=result["grounded"],
                matched=result["matched"],
                sources=[SourceCitation(**s) for s in result["sources"]],
                usage=result.get("usage", {}),
            )

        # Fallback: plain conversation with the LLM.
        try:
            reply, usage = await llm.complete_chat(settings, history, message)
        except LLMError as exc:
            logger.warning("chat failed: %s", exc.message)
            return JSONResponse({"error": exc.message}, status_code=exc.status_code)

        return ChatResponse(reply=reply, model=settings.llm_model, usage=usage)

    @app.post("/feedback", tags=["feedback"])
    async def feedback(request: Request) -> dict:
        enforce_rate_limit(request)
        try:
            body = await request.json()
        except Exception:
            body = {}
        logger.info("feedback: %s", body)
        return {"ok": True}

    @app.get("/", include_in_schema=False)
    async def index() -> dict:
        return {
            "service": "website-ai-chatbot",
            "health": "/health",
            "widget": "/widget.js",
            "knowledge_base": "/kb/status",
        }

    return app


app = create_app()
