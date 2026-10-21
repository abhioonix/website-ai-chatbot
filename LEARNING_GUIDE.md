# What I Built, and Why — a Walkthrough

A plain-language explanation of the whole chatbot project: the decisions, the
code, the mistakes, and the concepts. Written so you can reproduce it yourself.

It now runs as a **RAG** chatbot — it answers only from a knowledge base you
supply, with citations, and says so honestly when nothing matches. Parts 3, 4.5,
9 and 10 cover that addition; the rest describes the original v1 build.

---

## Part 1 — The problem, and the plan

**Goal:** add a floating AI chat widget to a website that already lives on AWS
(S3 + CloudFront + Lambda + API Gateway + DynamoDB), without disturbing any of
that existing infrastructure.

**The trap in the brief:** "add a single script tag to the existing HTML" sounds
easy, but two things make it not-trivial:

1. The site is a **built** app (Vite + React + TypeScript). Its real entry point
   is `frontend/index.html`, and the thing actually deployed is `frontend/dist/`.
   Editing `dist/index.html` would be silently overwritten on the next build.
2. The site **already has a floating button bottom-right** (the voice mic). A new
   chat widget in the same corner would sit exactly on top of it.

**The plan:**

| Step | What | Why |
|------|------|-----|
| 1 | Build the chatbot as a **completely separate project** | The brief says keep it independent. Separate = cannot break the existing site. |
| 2 | Host it on a **free tier that takes no credit card** | Requirement 1 of the brief. |
| 3 | Serve the widget from the **same service** as the API | One deploy, one URL, no extra static host to manage. |
| 4 | Put the widget in a **Shadow DOM** | Host page CSS cannot leak in; widget CSS cannot leak out. |
| 5 | Put the widget **bottom-left** on VaaniLink | Avoids the existing mic button at bottom-right. |
| 6 | Make the integration **inert until configured** | The site must never break if the chatbot URL isn't set yet. |

---

## Part 2 — Choosing the hosting provider (this is a real research task)

Free tiers change constantly, so I looked up the current terms before choosing.
Here's the honest picture as of now:

| Provider | Free tier? | Card required? | Behaviour | Verdict |
|----------|-----------|----------------|-----------|---------|
| **Render** | Yes — web services, 750 hrs/mo | **No** | Sleeps after 15 min idle, ~30–60 s cold start | ✅ **Chosen** |
| Koyeb | 1 free instance | **Yes** — $29 pre-auth hold since Feb 2026 | Scales to zero after ~1 hr | ❌ Needs card |
| Google Cloud Run | $200 trial credit, then paid | **Yes** — billing account | Always-free tier is tiny | ❌ Needs card |
| Fly.io | No free tier for new users | **Yes** | — | ❌ Needs card |
| Railway | No real free tier | — | Trial credits only | ❌ |
| Vercel | Yes (Hobby) | No | FastAPI becomes a *serverless function* with a short execution cap — an LLM call can exceed it | ⚠️ Wrong tool |

**Why Render won:**
1. No credit card — genuinely zero-cost to start.
2. Deploys straight from a Git repo with a `render.yaml` blueprint (one step).
3. Gives you a real public HTTPS URL.
4. Plain Python/ASGI — FastAPI runs unmodified.
5. Cheap to maintain.

**The honest trade-off:** the free service **sleeps after 15 minutes without
traffic**. The first message after a quiet period can take 30–60 seconds while it
wakes up. The widget handles this by showing the panel immediately and a friendly
error if the backend is still waking. If that's annoying later, the Starter plan
($7/mo) keeps it awake.

**Important distinction the brief asked for:** *free hosting* ≠ *free LLM calls*.
Render is free; the LLM API is a separate account with its own limits. See Part 9.

---

## Part 3 — The architecture

```
        Visitor's browser
              │
   ┌──────────┴───────────┐
   │  <script> loads      │
   │  widget.js           │
   │  (Shadow DOM)        │
   └──────────┬───────────┘
              │  POST /api/chat  (HTTPS, JSON)
              ▼
   ┌────────────────────────────────────────────┐
   │  Render (free tier)                        │
   │  FastAPI  ── app/main.py                   │
   │    ├─ /health    (LLM + knowledge-base)    │
   │    ├─ /widget.js                           │
   │    ├─ /kb/status /kb/rebuild               │
   │    └─ /api/chat                            │
   │         │                                  │
   │         ▼  RAG mode                        │
   │  app/kb/  retrieve ──► ground ──► answer   │
   │     │          │                  │        │
   │     │          ▼                  ▼        │
   │     │    Jina embeddings     Groq API      │
   │     │          │           (OpenAI-compat) │
   │     │          ▼                          │
   │     │      Qdrant Cloud                     │
   │     └──► knowledge_base/ (*.md,*.txt,...)  │
   └────────────────────────────────────────────┘
```

Key idea: the **backend is the only thing that knows the API keys**. The browser
never sees them. That's why the widget can be embedded on *any* public site safely.

**Second key idea:** in RAG mode the model is not asked to "know" anything. It is
handed a few retrieved passages and told to answer *only* from them. That is what
makes the answer trustworthy — and what lets the widget show a citation for it.

---

## Part 4 — The backend, piece by piece

### 4.1 `app/config.py` — configuration from the environment

Everything is read from environment variables. Nothing is hard-coded.

```python
self.llm_api_key   = os.getenv("LLM_API_KEY", "")
self.llm_base_url  = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
self.llm_model     = os.getenv("LLM_MODEL", "openai/gpt-oss-20b")
self.allowed_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "...").split(",")]
```

There's also a tiny `.env` loader for local dev. **Why write your own instead of
using `pydantic-settings`?** Fewer dependencies = fewer things to break, and the
logic is 6 lines. For a project this size that's the right call.

### 4.2 `app/main.py` — the FastAPI app

Three routes:

```python
@app.get("/health")     # liveness + tells you if the key is configured
@app.get("/widget.js")  # serves the widget script from static/
@app.post("/api/chat")  # the actual chat
```

**Three middleware/handler layers worth understanding:**

**(a) CORS** — Cross-Origin Resource Sharing. A *browser* mechanism that says
"only these origins may call this API from a web page."

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,   # NOT ["*"] in production
    allow_credentials=False,                   # we use no cookies
    allow_methods=["GET", "POST", "OPTIONS"],
)
```

> **Critical concept:** CORS is **not authentication**. It only stops *other
> websites* from calling your API via a visitor's browser. Anyone can still call
> it with `curl`. That's why you also need rate limiting (below).

**(b) Body-size limit** — reject huge requests before they reach your code:

```python
content_length = request.headers.get("content-length")
if content_length and int(content_length) > settings.max_body_bytes:
    return JSONResponse({"error": "Request too large."}, status_code=413)
```

**(c) Generic exception handler** — never leak internals:

```python
@app.exception_handler(Exception)
async def unhandled_handler(request, exc):
    logger.exception(...)                       # full detail goes to the SERVER log
    return JSONResponse({"error": "Something went wrong..."}, status_code=500)
```

> **This one was a real bug I found by testing.** Originally an unexpected
> exception would have crashed the handler and returned a raw traceback. The test
> forced me to add this. Good tests find real bugs.

### 4.3 `app/security.py` — rate limiting

A **fixed-window limiter** keyed by client IP:

```python
def check(self, client: str) -> tuple[bool, dict]:
    now = time.monotonic()
    cutoff = now - self.window_seconds          # 60s window
    while window.hits and window.hits[0] <= cutoff:
        window.hits.popleft()                    # drop expired hits
    if len(window.hits) >= self.limit:
        return False, {...}                      # over budget -> 429
    window.hits.append(now)
    return True, {...}
```

**Why not use Redis?** Because the free tier runs a **single process**. A shared
store would be needed only if you scaled to multiple instances. Keep it simple.
(If you later scale, swap this class for Redis — the interface stays the same.)

Note the `client_ip()` helper: behind Render's proxy, the real IP is in
`X-Forwarded-For`, not `request.client.host`.

### 4.4 `app/llm.py` — the provider-agnostic client

This is the clever part. Instead of using Groq's SDK, we speak the
**OpenAI-compatible HTTP protocol** directly:

```python
client = httpx.AsyncClient(
    base_url=settings.llm_base_url,               # any OpenAI-compatible host
    headers={"Authorization": f"Bearer {settings.llm_api_key}"},
)
response = await client.post("/chat/completions", json={
    "model": settings.llm_model,
    "messages": messages,
    "max_tokens": settings.max_output_tokens,
})
```

**Why?** Because then switching providers is a config change, not a code change.
Groq today, OpenRouter tomorrow, a local vLLM server next month — same code.

**History handling** — `build_messages()` does three safety things:

```python
allowed = {"user": 0, "assistant": 1}     # 1. drop anything else (incl. "system")
cleaned = cleaned[-settings.max_history_messages:]   # 2. keep only the newest N
messages = [{"role": "system", "content": settings.system_prompt}]  # 3. prepend OUR system prompt
```

> **Security concept:** a client could send `{"role": "system", "content": "ignore
> your instructions"}` and try to hijack the model. Step 1 blocks that. Step 3
> means *your* system prompt always wins.

**Error mapping** — every failure becomes a predictable status:

| Situation | Status | Client sees |
|-----------|--------|-------------|
| Timeout | 504 | "took too long to respond" |
| Network error | 502 | "could not reach the AI service" |
| Bad key (401/403) | 503 | "assistant is misconfigured" |
| Provider throttling (429) | 429 | "assistant is busy" |
| No key configured | 503 | "assistant is not configured yet" |

Notice: **the API key is never in any of these messages.**

### 4.5 `app/kb/` — the RAG layer (added after v1)

The original version just forwarded the question to the LLM. That works, but the
model answers from its *training data* — it doesn't know your product, and it will
confidently invent an answer when it doesn't. RAG fixes both problems.

**RAG = Retrieval-Augmented Generation.** Don't ask the model to know things.
Look up the relevant text first, hand it to the model, and let it quote.

The pipeline, in the order it runs:

```
load ──► chunk ──► embed ──► store ──► retrieve ──► ground ──► answer
```

| Stage | File | One-line job |
|-------|------|--------------|
| Load | `load.py` | Read `.md`/`.txt`/`.json`/`.pdf`; headings become section names |
| Chunk | `chunk.py` | Split into ~600-word pieces with 100-word overlap |
| Embed | `embed.py` | Turn each chunk into a 1024-number vector via Jina |
| Store | `store.py` | Save vectors in Qdrant under content-hash ids |
| Retrieve | `retrieve.py` | Find the 4 closest chunks to the question |
| Ground | `rag.py` | Build the prompt, demand an answer from *only* that context |
| Answer | `llm.py` | Call Groq, attach the citations |

**Why chunk at all?** Because you cannot put a whole knowledge base in a prompt.
Chunking means you only send the *relevant* 600 words, not 60,000. That is cheaper
and more accurate.

**Why the heading is prepended to each chunk.** This one is subtle and it cost me
a real bug. If a chunk's text is *"Open Settings, then Security, and choose Reset
PIN"* but the question is *"how do I reset my PIN"*, the words don't overlap much
and the match score is mediocre. If the chunk's text starts with the heading
*"Resetting your PIN — Open Settings, then Security..."*, the question now shares
key words with the chunk and scores far higher. Headings are the single cheapest
accuracy win in the whole system.

**Why content-hash ids?** `md5(chunk_text)[:16]`. Rebuilding the index after
editing one file re-embeds only the chunks whose text actually changed. Run it ten
times, you never get duplicates.

**Asymmetric embeddings.** Jina lets you declare *what* the text is:

```python
JINA_TASK_PASSAGE = "retrieval.passage"   # documents get this
JINA_TASK_QUERY   = "retrieval.query"     # questions get this
```

Documents and questions live in different "dialects" of language. Tagging each
side correctly measurably improves retrieval. It's one parameter and it matters.

**The refusal path.** If nothing clears `KB_MIN_SCORE` (0.5), `retrieve()` returns
an empty list and `rag.py` returns a fixed "I couldn't find that" message with
`sources: []`. The model is never asked to guess. This is the whole point: an
honest "I don't know" beats a fluent fabrication every time.

```python
if not chunks:
    return {"reply": NOT_FOUND_REPLY, "sources": [], "grounded": False, "matched": 0}
```

**The retrieval seam.** `retrieve.py` is deliberately the only place that knows
*how* chunks are found. Today it's plain vector similarity. Tomorrow it could be
hybrid (vector + keyword) or reranked — and `rag.py` would not change at all. That
is the payoff for putting the seam in one function.

---

## Part 5 — The widget (`static/widget.js`)

### 5.1 Why Shadow DOM?

A normal `<div>` inside a host page inherits that page's CSS. If the host has
`button { background: red }`, your widget's buttons turn red.

**Shadow DOM** creates a *separate, sealed* DOM tree with its own styles:

```js
var mount = el('div');
mount.id = 'ai-chatbot-widget-root';
var root = mount.attachShadow({ mode: 'open' });   // <-- the seal
root.appendChild(style);   // <style> inside the shadow root
```

Everything after that lives inside `root`, invisible to the host page's CSS and
JavaScript. I proved this works by loading the widget onto a test page with
deliberately hostile global CSS (`button { background: red !important; font-size: 30px !important; }`)
and checking the computed styles. Result:

```
launcherBg:      rgb(132, 204, 22)   <- widget's lime green, NOT host red
launcherRadius:  50%                  <- widget's round shape
launcherFontSize: 13.33px             <- NOT host's 30px
hostBtnBg:       rgb(255, 0, 0)       <- host page unaffected
```

Isolation works **both directions**.

### 5.2 Never inject HTML from the model

Every message is rendered with `textContent`, never `innerHTML`:

```js
function appendBubble(role, text, isError) {
  var bubble = el('div', 'cb-msg ' + (role === 'user' ? 'cb-user' : 'cb-bot'));
  var p = el('p', null, text);       // el() sets textContent
  bubble.appendChild(p);
  ...
}
```

> **Security concept:** if an LLM ever returned `<img src=x onerror=...>` and you
> used `innerHTML`, that script would run in your page. `textContent` makes it
> inert — it just displays as literal text.

### 5.3 The state machine

```
busy = false
  │ user clicks send
  ▼
busy = true  ──►  disable input + send button  ──►  show typing dots
  │                                                    │
  │                                          fetch POST /api/chat
  │                                                    │
  ├─ success ──► append assistant bubble, add to history
  └─ failure ──► append red error bubble, set offline indicator
  │
  ▼
busy = false  ──► re-enable input, refocus
```

History is kept in memory **and** mirrored to `sessionStorage`, so it survives a
page refresh but dies when the tab closes (no server-side retention).

---

## Part 6 — Testing: how I actually verified it

The brief said "don't claim success unless you verified it." Here's the ladder I
climbed — each step is stronger evidence than the last.

**Level 1 — Automated unit tests (`pytest -q`): 38 collected, 37 passed, 1 skipped**

The one skipped test is the opt-in live-LLM call; run it with
`CHATBOT_LIVE_TEST=1 pytest -q`.

Tests use FastAPI's `TestClient`. Crucially, the LLM is **monkeypatched** with a
stub so tests need no network and no API key:

```python
async def fake_complete(settings, history, user_message, *, client=None):
    return f"STUB[...]", {"prompt_tokens": 1}
monkeypatch.setattr("app.llm.complete_chat", fake_complete)
```

What the backend tests cover: health, widget serving, empty/overlong/unknown-field
rejection, history trimming, system-role injection blocked, upstream 502/503/504,
rate limiting → 429, oversized body → 413, CORS allow **and** block, and
"no stack trace leaks".

The RAG tests (`test_rag.py`, 19) run fully offline: a fake embedding function and
an in-memory Qdrant. They cover chunking and overlap, the prompt-budget trimmer,
retrieval ranking and the similarity floor, the refusal path when nothing
matches, citation building, idempotent rebuilds, and the grounded-answer prompt.

> **Real bug this caught:** the tests failed because `main.py` did
> `from .llm import complete_chat`, which *binds* the function at import time.
> Monkeypatching `app.llm.complete_chat` didn't affect the copy in `app.main`.
> Fix: call it as `llm.complete_chat(...)` so the lookup happens at call time.
> This is a genuinely important Python gotcha.

**Level 2 — Real server + real HTTP (`curl`)**

Started uvicorn and hit it:
```
GET  /health      -> {"status":"ok","llm_configured":true,"model":"openai/gpt-oss-20b",
                      "knowledge_base":{"enabled":false,"embeddings_configured":false,...}}
GET  /widget.js   -> 200, content-type: application/javascript, 15636 bytes
POST /api/chat    -> 400 (empty), 422 (extra field), 413 (oversized),
                     503 (no key), 429 (rate limited)
OPTIONS preflight -> allowed origin gets access-control-allow-origin;
                     evil origin gets 400 with no CORS headers
```

**Level 3 — Real LLM call**

```
POST /api/chat {"message":"What is the capital of France?"}
-> {"reply":"Paris.", "model":"openai/gpt-oss-20b", ...}

POST /api/chat with history -> "About 2.1 million residents live in the city proper..."
```

The second call proved **multi-turn context actually works** — it knew "its"
meant Paris.

**Level 3b — Real RAG call (the whole point)**

With Jina + Qdrant configured and the index built, the same endpoint changes
behaviour — no code change, just configuration:

```
GET  /kb/status   -> {"enabled":true,"embeddings_configured":true,
                      "vector_store_configured":true,"chunks_stored":15,...}

POST /api/chat {"message":"How do I reset my PIN?"}
-> {"reply":"Open Settings, then Security, and choose Reset PIN.",
    "grounded":true, "matched":3,
    "sources":[{"source":"vaanilink-faq.md","section":"Resetting your PIN","score":0.81}, ...]}

POST /api/chat {"message":"What is the capital of France?"}
-> {"reply":"I couldn't find that in the material available to me...",
    "grounded":false, "matched":0, "sources":[]}
```

The second answer is the one that matters. The question is *outside* the knowledge
base, so the model was never asked — it returned the fixed refusal with no
sources. That is the difference between a chatbot and a liability.

**Level 4 — Real browser (`browser_navigate`)**

Loaded a hostile-CSS host page, clicked the launcher, typed `What is 17 * 23?`,
sent it:
```
bubbles: ["Hello from the test host page.", "What is 17 * 23?", "17 × 23 = **391**"]
console errors: 0
```

Then killed the backend and sent another message:
```
{"err":"true","text":"Could not reach the assistant. Check your connection and try again."}
offline: true, subtitle: "Reconnecting…", input re-enabled
```

Error handling verified end-to-end.

**Level 5 — Real built app (before I reverted it)**

Built VaaniLink with `vite build`, served `dist/`, logged in, and measured the
two floating buttons:
```
mic button:  left 1200, right 1256, bottom 24   (bottom-right)
widget:      left 24,   right 80,   bottom 24   (bottom-left)
overlapping: false
console errors: 0
```

---

## Part 7 — The Vite environment-variable trick (and its trap)

VaaniLink is a **built** app, so the widget URL has to be injected at build time,
not written as a literal. Vite supports HTML env replacement:

```html
<script>
  var url = "%VITE_CHATBOT_URL%";   <!-- Vite replaces this at build time -->
</script>
```

Set `VITE_CHATBOT_URL` in `.env.production`, run `vite build`, and the built
`dist/index.html` contains the real URL. Clean.

**The trap I fell into.** My first version guarded against an unset variable like
this:

```js
var url = "%VITE_CHATBOT_URL%";
if (!url || url.indexOf("%VITE_CHATBOT_URL%") === 0) return;   // ← BUG
```

Vite replaced **both** occurrences, including the one inside the guard string:

```js
var url = "http://127.0.0.1:8000";
if (!url || url.indexOf("http://127.0.0.1:8000") === 0) return;  // always true!
```

The guard always matched, so the widget **never loaded**. The build reported
success and looked fine — only inspecting the *built output* caught it.

**The fix** — guard on a property of the value, not on the token:

```js
if (!url || url.charAt(0) === "%") return;
```

> **Lesson:** never write a build-token inside a string you also use for logic.
> And always inspect the *generated artifact*, not just the source.

---

## Part 8 — Solving the mic-button conflict

Your `App.tsx` has:

```jsx
<button className="fixed bottom-6 right-6 z-40 ..." aria-label="Add by voice">
```

`bottom-6 right-6` = 24px from the bottom, 24px from the right. My widget's
default is `bottom: 24px; right: 24px`. **Exact overlap.**

Solutions I considered:

| Option | Problem |
|--------|---------|
| Widget bottom-right, mic moved | Modifies existing working code |
| Widget bottom-right, mic moved up | Fragile; depends on button heights |
| **Widget bottom-left** | ✅ No conflict, no existing code touched |

So the widget takes a `data-position` attribute (`bottom-right` by default for
other sites) and VaaniLink passes `bottom-left`. Verified: no overlap, both work.

---

## Part 9 — Costs, honestly

**Hosting (Render free tier): £0 / $0**
- 750 compute hours/month
- Sleeps after 15 min idle → 30–60 s cold start
- No credit card required

**LLM API (Groq free tier): £0 / $0**
- No credit card required
- `openai/gpt-oss-20b` — free, with a requests-per-day cap
- `openai/gpt-oss-120b` — stronger, also free, lower daily cap
- If you blow past the free cap, Groq bills per token (fractions of a cent per
  1M tokens). For a personal/college project you will not get close.

**Total to run this: £0.** The only real cost is your attention.

**Embeddings (Jina AI free tier): £0 / $0**
- No credit card required
- ~1M tokens/month, 100 requests/minute
- `jina-embeddings-v3` — 1024 dimensions, runs in the cloud (no local model)

**Vector store (Qdrant Cloud free tier): £0 / $0**
- No credit card required, and the free tier is **permanent** (not a trial)
- 1 GB RAM / 4 GB disk — comfortably holds a small knowledge base
- Hosted, so nothing to run or back up yourself

> **Key distinction:** "free hosting" and "free LLM" are two separate accounts.
> A free host does not give you free AI calls. This project needs **four** free
> accounts — Render, Groq, Jina, Qdrant — and none of them asks for a card.

---

## Part 10 — What is left for you to do

The chatbot is built and fully tested locally (38 tests, 1 opt-in live). It is
**not deployed**, because deploying needs your Render account login. Steps:

1. Create a Render account (free, GitHub login) — https://render.com
2. Create a Groq API key — https://console.groq.com/keys
3. Create a **Jina** key (free, no card) — https://jina.ai/embeddings
4. Create a **Qdrant Cloud** cluster (free, permanent, no card) —
   https://cloud.qdrant.io → New → Free tier → copy the cluster URL + API key
5. Put all of them in `.env` locally, then build the index:

   ```bash
   cd /home/weirdvella/website-ai-chatbot
   python3 -m scripts.rebuild_index
   ```

6. Start the server and check a real grounded answer:

   ```bash
   ./scripts/dev.sh
   curl -s http://127.0.0.1:8000/kb/status
   curl -s -H "Content-Type: application/json" \
     -d '{"message":"<a question your KB actually answers>","history":[]}' \
     http://127.0.0.1:8000/api/chat
   ```

   Confirm `"grounded": true` and a non-empty `"sources"`. Then ask something
   *outside* the knowledge base and confirm you get the refusal with `sources: []`.
7. In Render: **New → Blueprint**, connect `/home/weirdvella/website-ai-chatbot`
8. When prompted, set:
   - `LLM_API_KEY` = your Groq key
   - `JINA_API_KEY` / `QDRANT_URL` / `QDRANT_API_KEY` = from steps 3–4
   - `ALLOWED_ORIGINS` = `https://d1jjj0lkvs3rt6.cloudfront.net`
9. Render deploys and gives you a URL like `https://website-ai-chatbot.onrender.com`
10. Trigger the first index build on the live server, then browser-test the widget
    to see the citation chips render
11. **Then** re-apply the VaaniLink integration (see below)

### Re-applying the VaaniLink integration later

`frontend/.env.production`:
```
VITE_CHATBOT_URL=https://website-ai-chatbot.onrender.com
```

`frontend/index.html`, inside `<head>`:
```html
<script>
  (function () {
    var url = "%VITE_CHATBOT_URL%";
    if (!url || url.charAt(0) === "%") return;
    url = url.replace(/\/+$/, "");
    var s = document.createElement("script");
    s.src = url + "/widget.js";
    s.setAttribute("data-api-url", url);
    s.setAttribute("data-position", "bottom-left");
    s.setAttribute("data-title", "VaaniLink Assistant");
    s.setAttribute("data-welcome", "Hi! How can I help you with VaaniLink today?");
    s.defer = true;
    document.head.appendChild(s);
  })();
</script>
```

Then `npx vite build` and deploy `dist/` to the S3 bucket as you normally do.

---

## Part 11 — The concepts worth remembering

| Concept | One-line version |
|---------|------------------|
| CORS | Browser-only rule about which sites may call an API. Not authentication. |
| Rate limiting | Budget per client IP. Stops one visitor exhausting your LLM quota. |
| Shadow DOM | A sealed sub-tree with its own styles. Stops CSS leaking both ways. |
| `textContent` vs `innerHTML` | The first can't run code; the second can. Always prefer the first. |
| Token limits | Cap input length, history turns, and output tokens so nobody can force huge/expensive requests. |
| Environment variables | Secrets live on the server, never in code, never in the browser. |
| Monkeypatching | Swap a function for a fake in tests so tests need no network. |
| Import binding gotcha | `from x import f` binds at import; `x.f()` resolves at call time. |
| Build tokens | `%VITE_X%` is replaced at build time — don't use the token inside logic. |
| Free tier ≠ free LLM | Hosting and AI inference are separate accounts with separate limits. |
| RAG | Don't ask the model to know things — look up the text first, then let it quote. |
| Chunking | Split documents so only the *relevant* ~600 words enter the prompt, not 60,000. |
| Embeddings | Turn text into numbers so "similar meaning" becomes "close together". |
| Asymmetric embeddings | Tag documents as `retrieval.passage` and questions as `retrieval.query`. |
| Vector store | A database that finds *nearby* vectors, not exact matches. |
| Content-hash ids | `md5(text)` as the id — re-running an index never duplicates rows. |
| Retrieval seam | Put "how we find chunks" in one function so the strategy can be swapped. |
| Refusal path | If nothing matches, say so. An honest "I don't know" beats a fluent invention. |
| Grounding | The model gets only the retrieved text; anything else is off-limits. |

---

## Part 12 — The mistakes I made (so you don't have to)

1. **Assumed `llama-3.1-8b-instant` was available.** It wasn't — the API
   returned `model_not_found`. Lesson: always list the models the key can
   actually see before picking a default.
2. **Monkeypatch binding bug** (Part 6). Caught by tests.
3. **Unhandled exceptions would have returned raw tracebacks.** Caught by tests.
4. **The Vite token guard bug** (Part 7). Caught by inspecting build output.
5. **Cloudflare blocked urllib's default user-agent** (`error code: 1010`).
   Fixed by sending a normal browser `User-Agent` header.
6. **The VaaniLink integration had to be reverted** because the backend isn't
   deployed yet — wiring it up pointed at a URL that doesn't exist.
7. **Tests became non-deterministic.** After I created a local `.env` for
   development, `test_health_ok` started failing because it asserted
   `llm_configured is False`. The test was depending on ambient credentials.
   Fix: the fixture now explicitly clears `llm_api_key`. **Lesson:** tests must
   set up their own state and never read whatever happens to be in the
   environment — otherwise they pass on one machine and fail on another.
8. **Qdrant `:memory:` gives every client its own private database.** Two separate
   store instances could not see each other's points, which made the RAG tests
   fail in a way that looked like a retrieval bug. Fix: share one local client per
   collection in `store.py`. **Lesson:** in-memory databases are per-connection,
   not per-process.
9. **Section headings were not part of the embedded text.** A question mirroring a
   heading ("how do I reset my PIN") scored *lower* than unrelated chunks. Fix:
   prepend the heading to the chunk body before embedding. **Lesson:** what you
   embed is what you can find. Retrieval quality is decided at index time.
10. **`KB_ENABLED` defaults to `false`, and nothing looked broken.** With the flag
    missing from `.env`, `/api/chat` still returned `200` — it had silently fallen
    back to plain-LLM mode, with no citations and no refusal behaviour. The
    `scripts/make_env.py` helper was also not writing the flag at all, so
    re-running it re-broke RAG. Fix: the helper now writes `KB_ENABLED=true`, and
    the pitfall is documented. **Lesson:** a silent fallback is worse than a loud
    error. Always check `/kb/status` before believing a feature works.
11. **Filling in the real credentials broke 5 tests that had passed all along.**
    The `test_api.py` fixture cleared only `llm_api_key`. Once a real `.env`
    supplied Jina + Qdrant keys, `rag_ready` became `True`, so `/api/chat` took the
    RAG branch and the mocked `llm.complete_chat` was never called — the
    error-path tests failed with `assert 200 == 503`. Fix: the fixture now also
    clears `jina_api_key`, `qdrant_url`, `qdrant_api_key`, `qdrant_local` and sets
    `kb_enabled=False`. **Lesson:** adding a second code path silently invalidates
    every fixture that was forcing the first one. When you add a branch, audit the
    fixtures.

Every one of these was found by *verifying*, not by assuming. That's the whole
point of the testing ladder in Part 6.
