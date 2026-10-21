DevChatBot — Project Resume Bookmark
=====================================
Last updated: 2026-10-21

RESUME KEYWORD: "KB-CHATBOT-RESUME"
(Say that and the agent will pick up from exactly this point.)


PROJECT INFO
------------
Path:      /home/weirdvella/website-ai-chatbot
Type:      Standalone AI chatbot served as an embeddable floating widget
Mode:      RAG — answers ONLY from your knowledge base, with citations
Hosting:   Render free tier (planned, NOT deployed yet)
LLM:       Groq (free, no card) — provider-agnostic via env vars
Embeddings: Jina AI (free, no card)
Vectors:   Qdrant Cloud (free, permanent, no card)
Docs:      README.md (how to use) · LEARNING_GUIDE.md (why it's built this way)


CURRENT STATE — Phase 1-7 COMPLETE, RAG VERIFIED LIVE
-----------------------------------------------------
38 collected, 37 passed, 1 skipped by default;
with CHATBOT_LIVE_TEST=1 -> 38 passed (real Groq call).

RAG IS LIVE AND VERIFIED (2026-10-21):
  Jina key + Qdrant cluster URL/key taken from Intern_15_PJT/AAAAAapi.txt and
  written into .env (scripted, secrets never printed). rag_ready = True.
  Index built: 15 documents -> 15 chunks -> 15 stored (collection website_kb).
  Verified end-to-end against the live services:
    "How do I reset my PIN?"      -> grounded true, matched 1, source
                                     vaanilink-faq.md / "How do I reset my PIN" (0.708)
    "Can I use VaaniLink in Hindi?" -> grounded true, matched 3, top score 0.8447
    "What is the capital of France?" -> refusal, grounded false, sources []
  Browser test (tests/testpage on :5173, backend on :8000): citation chip
    rendered and visually confirmed; the refusal showed no chip; 0 console errors.

DONE:
  Phase 1  Knowledge source loading  app/kb/load.py
           .md / .txt / .json / .pdf — headings become section names
           Sample KB lives in knowledge_base/ (3 files, 15 sections)
  Phase 2  Chunking                 app/kb/chunk.py
           sentence-aligned, 600 words, 100-word overlap
           section heading prepended to chunk text (critical for retrieval)
           content-hash ids -> re-indexing is idempotent
  Phase 3  Embeddings               app/kb/embed.py  (Jina, async)
           asymmetric task: retrieval.passage for docs, retrieval.query for queries
  Phase 4  Vector store             app/kb/store.py  (Qdrant)
           cloud mode via QDRANT_URL + key; local in-memory mode for tests
           shared local client per collection (see PITFALLS)
  Phase 5  Retrieval                app/kb/retrieve.py
           single seam: retrieve(query) -> chunks. Swap to hybrid later.
           similarity threshold + prompt char budget
  Phase 6  Grounded answering       app/kb/rag.py + app/llm.py
           system prompt forbids outside knowledge; explicit refusal when
           nothing matches; citations returned with every answer
  Index    Rebuild orchestration    app/kb/index.py + scripts/rebuild_index.py
  API      /health /widget.js /kb/status /kb/rebuild /api/chat
  Widget   static/widget.js — Shadow DOM, renders source citation chips
  Tests    tests/test_api.py (19) + tests/test_rag.py (19) = 38 (1 opt-in live)

NOT DONE YET:
  1. Deploy to Render — needs the user's Render login (steps in
     LEARNING_GUIDE.md Part 10 and README.md section 7)
  2. Re-apply the VaaniLink integration (reverted by request — snippet in
     LEARNING_GUIDE.md Part 10)
  3. Swap the sample knowledge_base/ content for the user's real documents
     (the 3 files there are VaaniLink samples), then rebuild the index


REMAINING (in order)
--------------------
  Step 8  Deploy to Render — needs the user's Render login. render.yaml is a
          Blueprint: New -> Blueprint -> connect this repo -> fill in the
          secrets (LLM_API_KEY, JINA_API_KEY, QDRANT_URL, QDRANT_API_KEY,
          KB_ADMIN_TOKEN, ALLOWED_ORIGINS). Then trigger the first index build:
            curl -X POST https://YOUR-HOST/kb/rebuild -H "x-kb-admin-token: TOKEN"
          Full steps: LEARNING_GUIDE.md Part 10 and README.md section 7.

  Step 9  Replace knowledge_base/ with the real documents, rebuild, re-test.

  Step 10 Re-apply the VaaniLink integration (snippet in LEARNING_GUIDE.md Part 10).


KEY FILES
---------
  app/config.py          all env-driven settings (LLM, Jina, Qdrant, KB, security)
  app/main.py            FastAPI routes + CORS + rate limit + error handlers
  app/llm.py             chat client + GROUNDED_SYSTEM_PROMPT
  app/models.py          request/response schemas incl. SourceCitation
  app/security.py        in-memory per-IP rate limiter
  app/kb/load.py         source file loader
  app/kb/chunk.py        chunker + prompt-budget trimmer
  app/kb/embed.py        Jina embedding client
  app/kb/store.py        Qdrant store (cloud + shared local)
  app/kb/retrieve.py     THE retrieval seam (swap this for hybrid later)
  app/kb/rag.py          retrieve -> ground -> answer -> cite
  app/kb/index.py        rebuild orchestration + status
  static/widget.js       Shadow-DOM widget with citation chips
  knowledge_base/        your knowledge source (currently 3 sample files)
  tests/test_api.py      19 backend tests (18 offline + 1 opt-in live)
  tests/test_rag.py      19 RAG tests (offline, fake embeddings + local Qdrant)
  scripts/rebuild_index.py  rebuild the vector index
  render.yaml            Render Blueprint


TECH STACK
----------
  Backend:    Python 3.13, FastAPI, uvicorn, httpx, pydantic
  Vectors:    qdrant-client 1.19.1 (Qdrant Cloud free tier)
  Embeddings: Jina AI API (jina-embeddings-v3, 1024 dims, no local model)
  LLM:        Groq API (openai/gpt-oss-20b), OpenAI-compatible HTTP
  Widget:     vanilla JS, Shadow DOM, zero dependencies
  No PyTorch, no sentence-transformers — that is why 512MB RAM is enough.


ENVIRONMENT VARIABLES (full list in .env.example)
--------------------------------------------------
  LLM_API_KEY          Groq key (filled in the local .env)
  LLM_MODEL            openai/gpt-oss-20b
  JINA_API_KEY         Jina key (filled in the local .env)
  JINA_EMBED_MODEL     jina-embeddings-v3
  QDRANT_URL           cluster URL (filled in the local .env)
  QDRANT_API_KEY       cluster key (filled in the local .env)
  QDRANT_COLLECTION    website_kb
  KB_ENABLED           true
  KB_SOURCE_DIR        knowledge_base
  KB_MIN_SCORE         0.5
  KB_ADMIN_TOKEN       optional, protects POST /kb/rebuild
  ALLOWED_ORIGINS      must include the real site origin


COSTS
-----
  Render free      $0  (750 hrs/mo, sleeps 15 min idle, no card)
  Jina free        $0  (~1M tokens/mo, 100 RPM, no card)
  Qdrant free      $0  (permanent, 1GB RAM / 4GB disk, no card)
  Groq free        $0  (no card, daily request cap)
  TOTAL            $0
  NOTE: free hosting != free LLM. These are four separate free accounts.


PITFALLS DISCOVERED (do not re-learn these the hard way)
--------------------------------------------------------
  1. Qdrant `:memory:` gives EVERY client its own private database. Separate
     store instances could not see each other's points. Fixed by sharing one
     local client per collection in app/kb/store.py.
  2. Section headings were NOT part of the embedded chunk text, so a question
     mirroring a heading ("how do I reset my PIN") scored LOWER than unrelated
     chunks. Fixed by prepending the heading to the chunk body.
  3. `from module import func` binds at import time, so monkeypatching
     `module.func` does not affect callers. All cross-module calls go through
     module attributes (llm.complete_chat, embed.embed_texts, ...) so tests
     can patch them.
  4. Tests must not depend on ambient credentials. The `settings` fixture clears
     llm_api_key explicitly — but that was NOT ENOUGH once RAG keys existed.
     See pitfall 8.
  5. The offline test embedding is a hash bag-of-words with IDF weighting;
     near-verbatim hits land around 0.4-0.6, so tests use a 0.35 floor while
     production uses 0.5 (real Jina embeddings score much higher).
  6. Cloudflare blocks urllib's default user-agent (error code 1010). Any
     direct HTTP call needs a browser-like User-Agent header.
  7. KB_ENABLED defaults to FALSE in app/config.py:60. If it is absent from
     .env, the app silently runs in plain-LLM mode with no citations and no
     refusal behaviour — /api/chat still returns 200, so nothing looks broken.
     Always check `rag_ready` via /kb/status before testing RAG. scripts/make_env.py
     now writes KB_ENABLED=true (fixed 2026-10-21; it previously omitted it).
  8. A real .env makes 5 backend tests fail with "assert 200 == 503". Cause: the
     test_api.py `settings` fixture cleared only llm_api_key, so with real Jina +
     Qdrant keys present rag_ready became True and /api/chat took the RAG branch —
     the mocked llm.complete_chat was never called, so the error-path tests got a
     real 200. Fix: the fixture now also clears jina_api_key, qdrant_url,
     qdrant_api_key, qdrant_local and sets kb_enabled=False. Lesson: when you add
     a second code path, every fixture that forces the first one must be updated.


VAANILINK INTEGRATION
---------------------
  Currently REVERTED at the user's request. VaaniLink is byte-for-byte original:
    /home/weirdvella/Intern_15_PJT/VaaniLink/frontend/index.html  (524 bytes)
    /home/weirdvella/Intern_15_PJT/VaaniLink/frontend/.env.production (78 bytes)
  To re-apply later: see LEARNING_GUIDE.md Part 10.
  Critical detail: the widget uses data-position="bottom-left" because VaaniLink's
  voice mic button is fixed bottom-6 right-6 in frontend/src/App.tsx.
