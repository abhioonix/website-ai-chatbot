# Backend Troubleshooting — FastAPI

This document covers FastAPI-specific application errors. Adapt the patterns here to your project structure.

---

## FastAPI app won't start

**Cause:** The module path is wrong, the file doesn't exist, or the working directory is incorrect.

**Fix:**
1. Run from the project root directory.
2. Verify `app/main.py` or your entry module exists.
3. Check the module path matches your project structure (e.g., `app.main:app` for `app/main.py`).
4. Verify Python environment has the package installed: `pip list | grep fastapi`.

**Common error:** `ModuleNotFoundError: No module named 'app'` — fix by installing dependencies and running from the correct root.

---

## CORS errors in browser

**Cause:** The browser blocks cross-origin requests by default.

**Fix:**
```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.com"],  # specific origins, not wildcard
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    allow_credentials=True,
)
```

**Production advice:** Use specific origins, not `"*"`. Credentialed requests (`allow_credentials=True`) cannot use wildcard origins.

---

## 422 Unprocessable Entity

**Cause:** Request body doesn't match the Pydantic schema.

**Fix:**
1. Check field types (string, int, float, bool, list, etc.).
2. Verify required fields are present.
3. Check that `Content-Type: application/json` header is set.
4. Use the `/docs` or `/redoc` endpoint to test requests interactively.

---

## Dependency injection and cleanup

**Cause:** Dependency not properly declared or not cleaned up.

**Fix:**
1. Use `Depends()` for shared dependencies like DB sessions or auth.
2. Use `yield` and put cleanup code after it (e.g., close DB session).
3. Dependencies are cached within one request by default.

---

## Background work

**Cause:** Heavy or long-running work in a request handler.

**Fix:**
1. Use `BackgroundTasks` for fire-and-forget work after the response.
2. Use Celery, RQ, or a message queue for heavy, retryable, long-running, or distributed jobs.

---

## Async vs sync endpoints

**Cause:** Blocking I/O inside an async endpoint.

**Fix:**
1. `def` runs in a threadpool; `async def` runs on the event loop.
2. Never call blocking I/O (`time.sleep()`, blocking network I/O, synchronous DB drivers) inside `async def`.
3. Use async-compatible clients (`httpx.AsyncClient`, `asyncpg`) or offload blocking work to a threadpool.

---

## Path and query parameters

**Cause:** Invalid parameter validation.

**Fix:**
1. Path params are part of the URL and required: `@app.get("/items/{item_id}")`.
2. Query params follow `?` and may have defaults: `@app.get("/items")`.
3. Use `Path()` or `Query()` for validation (length limits, numeric bounds, regex).

---

## WebSocket

**Fix:**
1. Define route: `@app.websocket("/ws")`.
2. Accept connection: `await websocket.accept()`.
3. Handle disconnects: catch `WebSocketDisconnect`.
4. Check proxy config for WebSocket upgrade headers.

---

## Error handling patterns

1. Use `try/except` in routes and return structured JSON errors.
2. Register exception handlers for global error handling (e.g., `@app.exception_handler(Exception)`).
3. Return consistent error response shape: `{"error": "human-readable message"}`.
4. Log the full exception with traceback for debugging (never return it to clients).

---

## Health check endpoint

**Fix:**
1. Expose `/health` returning 200 on success.
2. Use for load balancer and container orchestrator probes.
3. Separate liveness checks (process running) from readiness checks (dependencies available).
4. Optionally include dependency status (DB, Redis, queue) for readiness.

---

## Common FastAPI error codes

| Code | Name | Fix |
|---|---|---|
| 400 | Bad Request | Validate request body against Pydantic schema |
| 401 | Unauthorized | Provide valid `Authorization: Bearer` header |
| 403 | Forbidden | Check RBAC, API key scope, resource ownership |
| 404 | Not Found | Verify route path and base URL |
| 405 | Method Not Allowed | Configure allowed methods on route |
| 422 | Unprocessable Entity | Validate request body against Pydantic schema |
| 429 | Too Many Requests | Implement exponential backoff with jitter |
| 500 | Internal Server Error | Check backend logs, verify env vars, reproduce |
| 502 | Bad Gateway | Verify backend running, check proxy config |
| 503 | Service Unavailable | Check health endpoint, verify deps, retry with backoff |
| 504 | Gateway Timeout | Review timeout settings, identify slow component |
