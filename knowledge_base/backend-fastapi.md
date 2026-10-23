# Backend Troubleshooting — FastAPI

## FastAPI app won't start

If `uvicorn app.main:app` fails with "Could not import module", check that you are running from the project root and that `app/main.py` exists. The module path is `app.main:app` (file app/main.py, object app).

## CORS errors in browser

FastAPI blocks cross-origin requests by default. Add CORSMiddleware in app/main.py:

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

Always restrict origins in production. A wildcard origin with credentials is invalid.

## 422 Unprocessable Entity

FastAPI returns 422 when request body doesn't match the Pydantic schema. Check field types, required fields, and that you send JSON with Content-Type: application/json. Use the /docs endpoint to test.

## Dependency injection

Use Depends() for shared logic like DB sessions or auth. Dependencies are cached per request by default. Use yield for cleanup (e.g. close DB session).

## Background tasks

Use BackgroundTasks for fire-and-forget work after returning a response. For heavy jobs use Celery or RQ instead.

## Async vs sync endpoints

Defining an endpoint with `def` runs it in a threadpool; `async def` runs on the event loop. Never call blocking I/O (requests, time.sleep) inside async def — use httpx async or run_in_executor.

## Path and query parameters

Path params are required and part of the URL. Query params are optional with defaults. Use Query() for validation (min_length, regex, ge/le).

## WebSocket

Use @app.websocket("/ws"). Accept with await websocket.accept(). Handle disconnects with WebSocketDisconnect.
