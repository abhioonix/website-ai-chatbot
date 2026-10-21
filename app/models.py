"""Request/response models for the chat endpoint."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., description="Either 'user' or 'assistant'.")
    content: str = Field(..., description="Message text.")


class ChatRequest(BaseModel):
    message: str = Field(..., description="The visitor's new message.")
    history: list[ChatMessage] = Field(
        default_factory=list,
        description="Previous turns in the current session, oldest first.",
    )

    model_config = {"extra": "forbid"}


class SourceCitation(BaseModel):
    source: str
    section: str | None = None
    score: float | None = None


class ChatResponse(BaseModel):
    reply: str
    model: str
    grounded: bool = False
    matched: int = 0
    sources: list[SourceCitation] = Field(default_factory=list)
    usage: dict = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: str


class KBStatusResponse(BaseModel):
    enabled: bool
    embeddings_configured: bool
    vector_store_configured: bool
    collection: str
    chunks_stored: int
    source_dir: str


class RebuildResponse(BaseModel):
    ok: bool
    documents: int = 0
    chunks: int = 0
    stored: int = 0
    message: str = ""
