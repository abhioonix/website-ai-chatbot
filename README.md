# website-ai-chatbot

A small, standalone AI chatbot served as a floating widget that you drop into any
website with one `<script>` tag. It is completely independent of the site it lives
on — the host page needs no framework, no build changes, and no backend work.

It runs in **RAG mode**: it answers strictly from a knowledge base you supply,
with citations, and refuses honestly when nothing matches. If the knowledge base
is disabled or not configured, it falls back to plain conversation with the LLM.

* **Backend** — Python 3.13 + FastAPI, one process, no relational database.
* **Widget** — a single dependency-free `widget.js` served by the backend, isolated
  inside a Shadow DOM so host-page CSS and scripts cannot touch it.
* **AI** — any OpenAI-compatible chat-completions endpoint (Groq by default).
* **Retrieval** — Jina embeddings + Qdrant vector store, both free tier, no card.

---

## 1. How to embed it

```html
<script src="https://YOUR-CHATBOT-HOST/widget.js"
        data-api-url="https://YOUR-CHATBOT-HOST"
        data-position="bottom-right"
        data-title="Assistant"
        defer></script>
```

Drop that before `</body>`. Nothing else is required.

| Attribute       | Default                 | Meaning                                        |
|-----------------|-------------------------|------------------------------------------------|
| `data-api-url`  | origin of the script    | Backend base URL (no trailing slash)           |
| `data-position` | `bottom-right`          | `bottom-right` or `bottom-left`                |
| `data-title`    | `Assistant`             | Panel heading                                  |
| `data-accent`   | `#84cc16`               | Accent colour (CSS colour)                     |
| `data-placeholder` | `Ask anything…`      | Input placeholder                              |
| `data-welcome`  | generic greeting        | First assistant message                        |
| `data-history`  | `20`                    | Max turns kept in the session                  |

If the host page already has something in the bottom-right corner, use
`data-position="bottom-left"`.

---

## 2. API

| Method | Path           | Purpose                                              |
|--------|----------------|------------------------------------------------------|
| GET    | `/health`      | Liveness probe; reports LLM + knowledge-base status  |
| GET    | `/widget.js`   | The widget script                                    |
| GET    | `/kb/status`   | Is the knowledge base configured and indexed?        |
| POST   | `/kb/rebuild`  | Rebuild the vector index (needs `KB_ADMIN_TOKEN`)    |
| POST   | `/api/chat`    | Send a message, get an assistant reply               |

### POST /api/chat

Body:

```json
{
  "message": "How do I reset my PIN?",
  "history": [
    {"role": "user", "content": "previous question"},
    {"role": "assistant", "content": "previous answer"}
  ]
}
```

Response — RAG mode (knowledge base configured and indexed):

```json
{
  "reply": "Open Settings, then Security, and choose Reset PIN.",
  "model": "openai/gpt-oss-20b",
  "grounded": true,
  "matched": 3,
  "sources": [
    {"source": "vaanilink-faq.md", "section": "Resetting your PIN", "score": 0.81},
    {"source": "settings-guide.md", "section": "Security", "score": 0.74}
  ],
  "usage": {"total_tokens": 140}
}
```

`grounded` is `true` only when the answer came from the knowledge base. When
nothing relevant is retrieved, the API still returns `200` with `grounded: false`,
`matched: 0`, `sources: []`, and a refusal message — the model is never asked to
improvise.

Fallback mode (knowledge base off) omits the RAG fields and returns
`{"reply", "model", "usage"}`.

Errors always use the shape `{"error": "human-readable message"}` and never expose
API keys, stack traces, or internal details.

### GET /kb/status

```json
{
  "enabled": true,
  "embeddings_configured": true,
  "vector_store_configured": true,
  "collection": "website_kb",
  "chunks_stored": 15,
  "source_dir": "knowledge_base"
}
```

`enabled` here means **fully ready to answer** (`KB_ENABLED` on, both keys set).
It is `false` while the Jina or Qdrant keys are missing — that is the normal state
before the first index build, not a misconfiguration.

### POST /kb/rebuild

Rebuilds the index from the files in `KB_SOURCE_DIR`. Chunk ids are content
hashes, so re-running is idempotent — unchanged text is overwritten, not
duplicated. Requires the `x-kb-admin-token` header when `KB_ADMIN_TOKEN` is set.

```json
{"ok": true, "documents": 3, "chunks": 15, "stored": 15, "message": "Index rebuilt."}
```

---

## 3. The knowledge base (RAG)

The chatbot does not know anything until you give it documents. Drop files into
`knowledge_base/` and rebuild.

Supported formats: `.md`, `.txt`, `.json`, `.pdf` (PDF needs `pip install pypdf`).

Pipeline:

```
load  ->  chunk  ->  embed  ->  store  ->  retrieve  ->  ground  ->  answer
```

| Stage     | Module             | What it does                                                        |
|-----------|--------------------|---------------------------------------------------------------------|
| Load      | `app/kb/load.py`   | Reads source files; headings become section names                   |
| Chunk     | `app/kb/chunk.py`  | Sentence-aligned, 600 words, 100-word overlap, heading prepended    |
| Embed     | `app/kb/embed.py`  | Jina, async; `retrieval.passage` for docs, `retrieval.query` for questions |
| Store     | `app/kb/store.py`  | Qdrant collection; content-hash ids make rebuilds idempotent        |
| Retrieve  | `app/kb/retrieve.py` | Similarity threshold + prompt character budget                    |
| Answer    | `app/kb/rag.py`    | Grounds the answer in retrieved chunks, attaches citations          |

Two details that matter:

* **The section heading is prepended to each chunk's embedded text.** Without it,
  a question that mirrors a heading scores *lower* than unrelated chunks.
* **Chunk ids are content hashes**, so editing one file only re-embeds the
  chunks that actually changed.

### Rebuilding the index

```bash
python3 -m scripts.rebuild_index
```

Expected output:

```json
{"documents": 3, "chunks": 15, "stored": 15, "collection": "website_kb", "dimensions": 1024}
```

---

## 4. Configuration

Copy `.env.example` to `.env` locally, or set the same keys in your host's dashboard.

### LLM provider

| Variable                | Default                            | Purpose                              |
|-------------------------|------------------------------------|--------------------------------------|
| `LLM_API_KEY`           | _(required)_                       | Provider API key                     |
| `LLM_BASE_URL`          | `https://api.groq.com/openai/v1`   | Any OpenAI-compatible endpoint       |
| `LLM_MODEL`             | `openai/gpt-oss-20b`               | Model identifier                     |
| `LLM_TIMEOUT_SECONDS`   | `30`                               | Upstream request timeout             |

### Embeddings (Jina AI — free tier, no card)

| Variable             | Default                 | Purpose                                        |
|----------------------|-------------------------|------------------------------------------------|
| `JINA_API_KEY`       | _(required for RAG)_    | Jina API key                                   |
| `JINA_BASE_URL`      | `https://api.jina.ai/v1`| Jina endpoint                                  |
| `JINA_EMBED_MODEL`   | `jina-embeddings-v3`    | Embedding model                                |
| `JINA_EMBED_DIMS`    | `1024`                  | Vector dimensions — must match the model       |
| `JINA_TASK_PASSAGE`  | `retrieval.passage`     | Task for document chunks                       |
| `JINA_TASK_QUERY`    | `retrieval.query`       | Task for user questions                        |

### Vector store (Qdrant Cloud — free tier, permanent, no card)

| Variable             | Default                 | Purpose                                        |
|----------------------|-------------------------|------------------------------------------------|
| `QDRANT_URL`         | _(required for RAG)_    | Cluster URL, e.g. `https://xxx.cloud.qdrant.io:6333` |
| `QDRANT_API_KEY`     | _(required for RAG)_    | Cluster API key                                |
| `QDRANT_COLLECTION`  | `website_kb`            | Collection name                                |
| `QDRANT_LOCAL`       | `0`                     | Set `1` for in-memory local dev (no account)   |

### Knowledge base

| Variable                 | Default           | Purpose                                   |
|--------------------------|-------------------|-------------------------------------------|
| `KB_ENABLED`             | `false`           | **Master switch.** Off = plain LLM chat   |
| `KB_SOURCE_DIR`          | `knowledge_base`  | Folder of source documents                |
| `KB_CHUNK_SIZE`          | `600`             | Target chunk size in words                |
| `KB_CHUNK_OVERLAP`       | `100`             | Overlap between consecutive chunks        |
| `KB_TOP_K`               | `4`               | Chunks retrieved per question             |
| `KB_MIN_SCORE`           | `0.5`             | Cosine similarity floor                   |
| `KB_MAX_CONTEXT_CHARS`   | `4000`            | Max characters sent to the LLM            |
| `KB_ADMIN_TOKEN`         | _(empty)_         | Protects `POST /kb/rebuild`               |

> `KB_ENABLED` defaults to **false**. If it is missing from `.env`, the app runs
> in plain-LLM mode with no citations and no refusal behaviour — and `/api/chat`
> still returns `200`, so nothing looks broken. Check `/kb/status` before
> assuming RAG is working.

### Widget / security

| Variable                | Default                            | Purpose                              |
|-------------------------|------------------------------------|--------------------------------------|
| `ALLOWED_ORIGINS`       | `http://localhost:5173`            | Comma-separated CORS allow-list      |
| `RATE_LIMIT_PER_MINUTE` | `20`                               | Per-client-IP request budget         |
| `MAX_BODY_BYTES`        | `8192`                             | Request body size cap                |
| `MAX_INPUT_CHARS`       | `2000`                             | Per-message character cap            |
| `MAX_HISTORY_MESSAGES`  | `10`                               | Turns kept in context                |
| `MAX_OUTPUT_TOKENS`     | `512`                              | Cap on generated tokens              |
| `HOST` / `PORT`         | `0.0.0.0` / `8000`                 | Bind address                         |

---

## 5. Running locally

```bash
pip install -r requirements.txt
python3 scripts/make_env.py          # optional: fills .env from your existing Groq key
python3 -m scripts.rebuild_index  # builds the vector index (needs Jina + Qdrant keys)
./scripts/dev.sh                     # http://127.0.0.1:8000
```

Open `tests/testpage/index.html` via any static server on port 5173 to see the
widget embedded in a page that deliberately applies hostile global CSS.

Check readiness:

```bash
curl -s http://127.0.0.1:8000/kb/status
```

---

## 6. Tests

```bash
pytest -q                       # 37 tests, no network needed
CHATBOT_LIVE_TEST=1 pytest -q   # additionally performs one real provider call
python3 scripts/live_check.py   # standalone live provider check
```

The RAG tests use fake embeddings and an in-memory Qdrant, so they run offline.

---

## 7. Deployment

### Render (recommended)

`render.yaml` is a Render Blueprint. In the Render dashboard: **New → Blueprint**,
connect this repository, and fill in the secret values when prompted:
`LLM_API_KEY`, `JINA_API_KEY`, `QDRANT_URL`, `QDRANT_API_KEY`, `KB_ADMIN_TOKEN`
and `ALLOWED_ORIGINS`. Render builds and starts the service automatically.

The free plan:

* No credit card required.
* 750 compute hours/month.
* The service **sleeps after 15 minutes without traffic** and takes roughly
  30–60 seconds to wake up on the next request. The widget shows the panel
  immediately and displays a friendly error if the backend is still waking.

After the first deploy, rebuild the index once:

```bash
curl -X POST https://YOUR-CHATBOT-HOST/kb/rebuild \
  -H "x-kb-admin-token: YOUR_TOKEN"
```

### Manual alternative

Any host that can run a Python ASGI app works:

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Set `ALLOWED_ORIGINS` to the real origin of the site embedding the widget.

---

## 8. Security notes

* CORS restricts which origins may call `/api/chat`. CORS is a browser
  enforcement mechanism, not authentication — the endpoint is also protected by
  per-IP rate limiting, body-size caps, message-length caps, and bounded history.
* API keys live only in server-side environment variables. They are never sent
  to the browser, never stored in `localStorage`, and never written to logs.
* Message content is not logged or persisted; conversation history lives only in
  the visitor's `sessionStorage` and is cleared when the tab closes.
* Error responses are generic. Internal exceptions are logged server-side but
  returned to the client as a plain 500 message.
* Citation chips in the widget are built with `textContent`, never `innerHTML`,
  so retrieved text cannot inject markup into the host page.

---

## 9. Project layout

```
website-ai-chatbot/
├── app/
│   ├── config.py      environment-driven settings
│   ├── llm.py         provider-agnostic chat client + grounded-answer prompt
│   ├── main.py        FastAPI app and routes
│   ├── models.py      request/response schemas (incl. SourceCitation)
│   ├── security.py    rate limiter
│   └── kb/
│       ├── load.py      source file loader (.md/.txt/.json/.pdf)
│       ├── chunk.py     chunker + prompt-budget trimmer
│       ├── embed.py     Jina embedding client
│       ├── store.py     Qdrant store (cloud + in-memory local)
│       ├── retrieve.py  the retrieval seam (swap for hybrid later)
│       ├── rag.py       retrieve -> ground -> answer -> cite
│       └── index.py     rebuild orchestration + status
├── static/
│   └── widget.js      embeddable Shadow-DOM widget with citation chips
├── knowledge_base/    your documents (currently 3 sample files)
├── tests/
│   ├── test_api.py    19 backend tests (18 offline + 1 opt-in live)
│   ├── test_rag.py    19 RAG tests (offline)
│   └── testpage/      hostile-CSS page for manual widget checks
├── scripts/           dev helpers (local .env, index rebuild, live check)
├── render.yaml        Render Blueprint
├── requirements.txt
└── .env.example
```
