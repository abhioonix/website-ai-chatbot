"""RAG test suite — retrieval, grounding, refusal, and citations.

Runs fully offline: embeddings are replaced with a deterministic bag-of-words
vector and the vector store runs in Qdrant's in-memory mode. No network, no keys.
"""
from __future__ import annotations

import hashlib
import math
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.kb.chunk import chunk_documents, truncate_for_prompt
from app.kb.load import load_documents
from app.kb.retrieve import build_context, retrieve
from app.kb.rag import NOT_FOUND_REPLY, answer_from_knowledge_base
from app.main import create_app

KB_DIR = Path(__file__).resolve().parent.parent / "knowledge_base"


# --------------------------------------------------------------------------
# Deterministic fake embeddings
#
# Hash bag-of-words with IDF weighting, so rare terms ("PIN") count far more
# than common ones ("the"). This mimics how a real embedding model behaves —
# a near-verbatim question scores high, unrelated text scores near zero — while
# staying fully offline and reproducible.
# --------------------------------------------------------------------------
_IDF: dict[str, float] = {}


def _build_idf() -> None:
    from app.kb.chunk import chunk_documents

    docs = [c.text for c in chunk_documents(load_documents(KB_DIR), chunk_size=600, overlap=100)]
    total = max(1, len(docs))
    df: dict[str, int] = {}
    for doc in docs:
        for token in set(re.findall(r"[a-z0-9]+", doc.lower())):
            df[token] = df.get(token, 0) + 1
    _IDF.update({t: math.log((total + 1) / (c + 1)) + 1.0 for t, c in df.items()})


def fake_vector(text: str, dim: int) -> list[float]:
    if not _IDF:
        _build_idf()

    vec = [0.0] * dim
    for token in re.findall(r"[a-z0-9]+", text.lower()):
        weight = _IDF.get(token, 4.0)  # unseen terms: moderate weight
        digest = int(hashlib.sha1(token.encode()).hexdigest()[:8], 16)
        vec[digest % dim] += weight

    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


async def fake_embed_texts(settings, texts, *, task, client=None):  # noqa: ANN001
    return [fake_vector(t, settings.jina_embed_dims) for t in texts]


async def fake_embed_query(settings, query):  # noqa: ANN001
    return fake_vector(query, settings.jina_embed_dims)


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _isolate_local_store():
    """Give every test a clean local vector store."""
    from app.kb.store import reset_local_clients

    reset_local_clients()
    yield
    reset_local_clients()


@pytest.fixture()
def kb_settings() -> Settings:
    s = Settings()
    s.llm_api_key = ""               # never depend on ambient credentials
    s.kb_enabled = True
    s.jina_api_key = "test-jina-key"
    s.jina_embed_dims = 512          # larger = fewer hash collisions in tests
    s.qdrant_local = True
    s.qdrant_collection = "test_kb"
    s.kb_source_dir = str(KB_DIR)
    # The offline test embedding is a hash bag-of-words, so near-verbatim hits
    # land around 0.4-0.6. Production uses real Jina embeddings, which score
    # much higher, so 0.5 is the right floor there — see .env.example.
    s.kb_min_score = 0.35
    s.kb_top_k = 4
    return s


@pytest.fixture()
def fake_embeddings(monkeypatch, kb_settings):  # noqa: ARG001
    monkeypatch.setattr("app.kb.embed.embed_texts", fake_embed_texts)
    monkeypatch.setattr("app.kb.embed.embed_query", fake_embed_query)
    return fake_embed_texts


@pytest.fixture()
async def indexed(kb_settings, fake_embeddings):  # noqa: ARG001
    """A populated local index."""
    from app.kb.index import rebuild_index

    await rebuild_index(kb_settings)
    return kb_settings


# --------------------------------------------------------------------------
# Loading & chunking
# --------------------------------------------------------------------------
def test_load_documents_from_sample_kb():
    docs = load_documents(KB_DIR)
    assert len(docs) >= 5, "expected several sections from the sample knowledge base"
    assert any(d.source == "vaanilink-faq.md" for d in docs)
    assert all(d.text.strip() for d in docs)


def test_markdown_headings_become_sections():
    docs = load_documents(KB_DIR)
    faq = [d for d in docs if d.source == "vaanilink-faq.md"]
    assert any(d.section and "PIN" in d.section for d in faq)


def test_chunking_keeps_text_and_metadata():
    docs = load_documents(KB_DIR)
    chunks = chunk_documents(docs, chunk_size=50, overlap=10)
    assert chunks
    assert all(c.text.strip() for c in chunks)
    assert all(c.source for c in chunks)
    # ids are stable
    assert len({c.id for c in chunks}) == len(chunks)


def test_chunk_ids_are_content_addressed():
    docs = load_documents(KB_DIR)
    a = chunk_documents(docs, chunk_size=50, overlap=10)
    b = chunk_documents(docs, chunk_size=50, overlap=10)
    assert [c.id for c in a] == [c.id for c in b]


def test_truncate_for_prompt_respects_budget():
    from app.kb.chunk import Chunk

    chunks = [Chunk(id=str(i), text="x" * 500, source="s.md", section=None, order=i) for i in range(10)]
    kept = truncate_for_prompt(chunks, max_chars=1200)
    assert kept
    assert sum(len(c.text) for c in kept) <= 1200 + 200 * len(kept)


# --------------------------------------------------------------------------
# Retrieval
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_retrieve_finds_relevant_chunk(indexed):  # noqa: ARG001
    hits = await retrieve("how do I reset my PIN", indexed)
    assert hits, "expected a hit for a question straight from the FAQ"
    assert any("PIN" in h.text for h in hits)


@pytest.mark.asyncio
async def test_retrieve_ranks_best_match_first(indexed):  # noqa: ARG001
    hits = await retrieve("microphone button not working", indexed, min_score=0.0)
    assert hits
    assert hits == sorted(hits, key=lambda h: h.score, reverse=True)


@pytest.mark.asyncio
async def test_retrieve_returns_nothing_for_gibberish(indexed):  # noqa: ARG001
    hits = await retrieve("zzzz qqqq xyzzy", indexed, min_score=0.5)
    assert hits == []


@pytest.mark.asyncio
async def test_retrieve_drops_low_similarity(indexed):  # noqa: ARG001
    """A strict threshold must filter out weak matches."""
    hits = await retrieve("what is the capital of France", indexed, min_score=0.9)
    assert hits == []


# --------------------------------------------------------------------------
# Grounded answering
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_rag_returns_sources(indexed, monkeypatch):  # noqa: ARG001
    async def fake_answer(settings, context, question, history, *, client=None):  # noqa: ANN001, ARG001
        assert "PIN" in context
        return "Open Settings, choose Security, then Reset PIN.", {"total_tokens": 1}

    monkeypatch.setattr("app.kb.rag.llm.generate_grounded_answer", fake_answer)

    result = await answer_from_knowledge_base("how do I reset my PIN", [], indexed)
    assert result["grounded"] is True
    assert result["sources"], "expected at least one citation"
    assert any(s["source"] == "vaanilink-faq.md" for s in result["sources"])
    assert result["matched"] >= 1


@pytest.mark.asyncio
async def test_rag_refuses_when_nothing_matches(indexed, monkeypatch):  # noqa: ARG001
    called = False

    async def fake_answer(*a, **k):  # noqa: ANN001, ANN002, ANN202
        nonlocal called
        called = True
        return "should not be used", {}

    monkeypatch.setattr("app.kb.rag.llm.generate_grounded_answer", fake_answer)

    result = await answer_from_knowledge_base("zzzz qqqq xyzzy", [], indexed)
    assert result["grounded"] is False
    assert result["sources"] == []
    assert result["reply"] == NOT_FOUND_REPLY
    assert called is False, "the LLM must not be called when there is no evidence"


@pytest.mark.asyncio
async def test_context_block_is_bounded(indexed):  # noqa: ARG001
    hits = await retrieve("PIN", indexed, top_k=4, min_score=0.0)
    context = build_context(hits, max_chars=500)
    assert context.startswith("[1] Source:")
    assert len(context) <= 500 + 400


# --------------------------------------------------------------------------
# API surface
# --------------------------------------------------------------------------
@pytest.fixture()
def rag_client(indexed):  # noqa: ARG001
    with TestClient(create_app(indexed)) as client:
        yield client


def test_health_reports_knowledge_base(rag_client):
    r = rag_client.get("/health")
    assert r.status_code == 200
    kb = r.json()["knowledge_base"]
    assert kb["enabled"] is True
    assert kb["chunks_stored"] > 0


def test_kb_status_endpoint(rag_client):
    r = rag_client.get("/kb/status")
    assert r.status_code == 200
    assert r.json()["chunks_stored"] > 0


def test_kb_rebuild_endpoint(rag_client):
    r = rag_client.post("/kb/rebuild")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["stored"] > 0


def test_kb_rebuild_requires_token_when_configured(kb_settings, fake_embeddings):  # noqa: ARG001
    import os

    os.environ["KB_ADMIN_TOKEN"] = "secret-token"
    try:
        kb_settings = Settings()
        kb_settings.llm_api_key = ""
        kb_settings.kb_enabled = True
        kb_settings.jina_api_key = "test-key"
        kb_settings.jina_embed_dims = 128
        kb_settings.qdrant_local = True
        kb_settings.kb_source_dir = str(KB_DIR)
        kb_settings.kb_min_score = 0.0

        with TestClient(create_app(kb_settings)) as client:
            assert client.post("/kb/rebuild").status_code == 403
            ok = client.post("/kb/rebuild", headers={"x-kb-admin-token": "secret-token"})
            assert ok.status_code == 200
    finally:
        os.environ.pop("KB_ADMIN_TOKEN", None)


def test_api_chat_returns_sources(rag_client, monkeypatch):
    async def fake_answer(settings, context, question, history, *, client=None):  # noqa: ANN001, ARG001
        return "Open Settings, choose Security, then Reset PIN.", {"total_tokens": 1}

    monkeypatch.setattr("app.kb.rag.llm.generate_grounded_answer", fake_answer)

    r = rag_client.post("/api/chat", json={"message": "how do I reset my PIN", "history": []})
    assert r.status_code == 200
    body = r.json()
    assert body["grounded"] is True
    assert body["sources"], "expected citations in the API response"


def test_api_chat_refuses_out_of_scope(rag_client, monkeypatch):
    async def fake_answer(*a, **k):  # noqa: ANN001, ANN002, ANN202
        raise AssertionError("LLM must not be called for an out-of-scope question")

    monkeypatch.setattr("app.kb.rag.llm.generate_grounded_answer", fake_answer)

    r = rag_client.post("/api/chat", json={"message": "zzzz qqqq xyzzy", "history": []})
    assert r.status_code == 200
    assert r.json()["grounded"] is False
    assert r.json()["sources"] == []


def test_api_chat_falls_back_when_rag_disabled(monkeypatch):
    """With KB_ENABLED=false the app must still answer, just without citations."""
    s = Settings()
    s.llm_api_key = "test-llm-key"
    s.kb_enabled = False
    s.allowed_origins = ["http://localhost:5173"]

    async def fake_complete(settings, history, message, *, client=None):  # noqa: ANN001, ARG001
        return "plain answer", {}

    monkeypatch.setattr("app.llm.complete_chat", fake_complete)

    with TestClient(create_app(s)) as client:
        r = client.post("/api/chat", json={"message": "hello", "history": []})
    assert r.status_code == 200
    assert r.json()["grounded"] is False
    assert r.json()["sources"] == []
