# Backend Error Codes and Troubleshooting Guide

> **Purpose:** A general-purpose reference for diagnosing common backend authentication, API, Python, FastAPI, Node.js/Express, database, server, Git, Docker, and deployment issues across AWS, GCP, Azure, and self-hosted environments.
>
> **Important:** Not every issue below has a numeric error code. HTTP status codes are standardized response codes; messages such as `ModuleNotFoundError` and `EADDRINUSE` are runtime or operating-system errors.

---

## Quick Reference: HTTP Status Codes

|| Code | Name | What it means | First checks |
|---|---|---|---|---|
| `400` | Bad Request | The request is invalid or malformed. | Check request syntax, parameters, and JSON formatting. |
| `401` | Unauthorized | Authentication is missing, invalid, or expired. | Check the token, signature, expiry, and authentication header. |
| `403` | Forbidden | The caller is authenticated but lacks permission, or access is otherwise denied. | Check roles, permissions, scopes, and route guards. |
| `404` | Not Found | The requested resource or route cannot be found. | Check the URL, route registration, and resource ID. |
| `409` | Conflict | The request conflicts with the current resource state. | Check duplicate records, version conflicts, and resource state. |
| `422` | Unprocessable Entity | The server cannot process the request data as provided. | Compare the request body and parameters with the validation schema. |
| `429` | Too Many Requests | The client has exceeded a rate limit. | Check request frequency and the rate-limit policy; respect `Retry-After` when provided. |
| `500` | Internal Server Error | An unexpected server-side failure occurred. | Inspect application logs and the traceback. |
| `502` | Bad Gateway | A proxy or gateway received an invalid response from an upstream server. | Check whether the application is running and whether the proxy target is correct. |
| `503` | Service Unavailable | The service is temporarily unavailable or overloaded. | Check service health, deployment status, maintenance state, and capacity. |
| `504` | Gateway Timeout | A proxy or gateway did not receive a timely response from an upstream server. | Check upstream latency, timeouts, database queries, and service health. |

---

## 1. Authentication and Sessions

### `401 Unauthorized` with a valid-looking token

**Possible causes**
- The token has expired or is not being sent correctly.
- The token is malformed or uses the wrong algorithm.
- The signing key or issuer/audience claims don't match.
- The token was issued by a different authority.

**Fix**
1. Check token expiry and claims.
2. Confirm the client sends `Authorization: Bearer <token>`.
3. Verify signing key, issuer, audience, and algorithm.
4. Refresh the token or re-login.
5. Keep secrets (signing keys, API keys) in environment variables or a secrets manager.

### `403 Forbidden`

**Possible causes**
- Missing role or permission scope.
- Resource ownership mismatch.
- Route guard not applied.
- Hosting/security policy or proxy rule blocks access.

**Fix**
1. Check role/permission assignments.
2. Verify resource ownership.
3. Apply route guards consistently.
4. Review security logs for the denied action.
5. Do not disable security controls as a first fix.

### Token / Key Management

**Common issues**
- `JWT` signing key mismatch.
- Expired tokens.
- API key not set, wrong format, or not sent.
- Credentials stored in code instead of environment variables.

**Fix**
1. Keep secrets in env vars or a secrets manager (AWS Secrets Manager, HashiCorp Vault, etc.).
2. Verify env vars are set in the deployment environment.
3. Rotate keys on exposure.
4. Check token signing algorithms (HS256 vs RS256) match between issuer and verifier.

---

## 2. API Errors (Request / Response)

### `400 Bad Request`

**Fix:**
1. Validate request syntax, parameters, and JSON formatting.
2. Check required fields and data types.
3. Check content-type header (`application/json`).

### `404 Not Found`

**Fix:**
1. Verify the URL, route registration, and resource ID.
2. Check the backend base URL and path.
3. Confirm the deployment version matches the client.

### `405 Method Not Allowed`

**Fix:**
1. Check the HTTP method used.
2. Configure allowed methods on the route.
3. Return the proper `Allow` header.

### `409 Conflict`

**Fix:**
1. Check for duplicate records.
2. Use unique constraints to prevent conflicts.
3. Return a clear conflict message with details.

### `413 Payload Too Large`

**Fix:**
1. Reduce body size.
2. Send only needed data.
3. Check server, proxy, and platform limits.

### `415 Unsupported Media Type`

**Fix:**
1. Send the expected `Content-Type` header.
2. Verify the parser or upload handler is enabled.

### `422 Unprocessable Entity`

**Fix:**
1. Compare the request body and parameters with the validation schema.
2. Check field types, required fields, and format constraints.

### `429 Too Many Requests`

**Fix:**
1. Respect `Retry-After`.
2. Use exponential backoff with jitter.
3. Debounce rapid frontend input.
4. Check rate-limit settings in the deployment config.

### `500 Internal Server Error`

**Fix:**
1. Inspect application logs and the traceback.
2. Verify environment variables are set correctly.
3. Reproduce with the same request/body.
4. Check recent changes (deploy, config, dependency).
5. Never expose secrets or stack traces to end users.

### `502 Bad Gateway`

**Fix:**
1. Verify the application is running.
2. Check whether the proxy target is correct (host, port).
3. Verify the backend is healthy.

### `503 Service Unavailable`

**Fix:**
1. Check service health (health endpoint).
2. Verify deployment status and maintenance mode.
3. Check capacity (CPU, memory, disk).
4. Verify external dependencies (database, cache, queue, AI provider) are available.
5. Retry after a delay with exponential backoff.

### `504 Gateway Timeout`

**Fix:**
1. Check upstream latency.
2. Review timeouts in the backend, proxy, and hosting platform.
3. Check database query performance.
4. Verify the AI provider or external service is responding.
5. Retry safely after a delay.

---

## 3. Python-Specific Errors

### `ModuleNotFoundError`

**Cause:** Python cannot find the module.

**Fix:**
1. Run from the project root directory.
2. Ensure the virtual environment is activated.
3. Install dependencies: `pip install -r requirements.txt`.
4. Check `sys.path` includes the project root.
5. Verify `__init__.py` is present in packages.

### `ImportError: cannot import name`

**Cause:** Circular import or name mismatch.

**Fix:**
1. Check spelling and that the symbol exists in the source module.
2. Avoid top-level imports that trigger circular dependencies.
3. Move imports inside functions or classes.
4. Check that the package is installed.

### `TypeError: unsupported operand type(s)`

**Cause:** Attempting an operation on incompatible types.

**Fix:**
1. Verify variable types.
2. Convert types explicitly.
3. Check API response data types match expectations.

### `ValueError: invalid literal`

**Cause:** Converting a string to a number or value fails.

**Fix:**
1. Check string content (whitespace, special chars, encoding).
2. Verify expected range/format.
3. Use `try/except ValueError` for graceful handling.
4. Validate input before conversion.

### `KeyError: 'key'`

**Cause:** Accessing a dictionary key that doesn't exist.

**Fix:**
1. Check if the key exists or use `dict.get('key')`.
2. Use `try/except KeyError` for graceful handling.
3. Verify the data source (API response, JSON, env vars).

### `IndexError: list index out of range`

**Cause:** Accessing an index beyond the list length.

**Fix:**
1. Check list length before accessing.
2. Verify API response data structure.
3. Add bounds checking in loops and range access.

### `AttributeError: 'module' has no attribute 'name'`

**Cause:** Accessing a non-existent attribute.

**Fix:**
1. Check the module or object has the attribute.
2. Verify the import path (module vs. class vs. function).
3. Check for typos and installed version compatibility.

### `FileNotFoundError`

**Cause:** File does not exist at the expected path.

**Fix:**
1. Verify the path is correct.
2. Check the file exists.
3. Use `os.path.join()` for cross-platform path construction.
4. Allow environment variable override for config paths.

### `PermissionError: [Errno 13] Permission denied`

**Cause:** File or directory permissions prevent access.

**Fix:**
1. Check permissions.
2. Verify the running user has read/write access.
3. On external drives (exFAT/NTFS), be aware of filesystem limitations (no symlinks).

### `OSError: [Errno 98] Address already in use`

**Cause:** Port already occupied.

**Fix:**
1. Find the process: `lsof -i :<port>` or `ss -tlnp`.
2. Kill the process or change the port.
3. Check for multiple instances of the app.

### `ConnectionRefusedError: [Errno 61] Connection refused`

**Cause:** Target service is not running or not listening.

**Fix:**
1. Verify the target service is running.
2. Check host/port in the connection string.
3. For Docker, use the container name as host.
4. Check firewall rules and security groups.

### `TimeoutError` / `socket.timeout`

**Cause:** Operation took longer than the timeout limit.

**Fix:**
1. Review timeout settings in config.
2. Check if the target service is slow or overloaded.
3. Increase timeout if the operation legitimately takes longer.
4. Add retry logic with exponential backoff.

### `MemoryError`

**Cause:** Exceeded available RAM.

**Fix:**
1. Reduce workload size or increase memory limits.
2. Profile memory usage with `memory-profiler` or `tracemalloc`.
3. Fix memory leaks: unbounded caches, retained references, accumulating listeners.
4. Restart as temporary mitigation.

### Python debugging tips

1. **Logging:** Use the `logging` module with levels (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).
2. **Stack traces:** Read bottom-up; the last frame is where the error originated.
3. **Breakpoints:** Use `breakpoint()` (Python 3.7+) or `import pdb; pdb.set_trace()`.
4. **Profiling:** Use `py-spy` for CPU profiling, `memory-profiler` for memory.
5. **Type checking:** Run `mypy` to catch type errors early.
6. **Linting:** Use `ruff` or `flake8` to catch style and potential bugs.

---

## 4. Node.js / Express-Specific Errors

### `npm install` fails

**Fix:**
1. Clear cache: `npm cache clean --force`.
2. Delete `node_modules` and `package-lock.json`, then run `npm install`.
3. Check Node version matches `package.json` `engines` field.
4. Use `nvm` to switch versions.
5. If native modules fail: `npm rebuild` or install build tools.

### `EADDRINUSE: port already in use`

**Fix:**
1. Find the process: `lsof -i :3000` (Linux/Mac) or `netstat -ano | findstr :3000` (Windows).
2. Kill the process or change the `PORT` environment variable.

### `Cannot find module`

**Cause:** Dependencies not installed, wrong path, or CommonJS/ESM mismatch.

**Fix:**
1. Run `npm install`.
2. Verify `require()` or `import` paths are relative (`./`) for local files.
3. For ES modules, ensure `"type": "module"` is set in `package.json`.
4. For dynamic imports, wrap in `async` function and use `await import()`.

### Express middleware order

**Fix:**
1. Register parsers (`express.json()`) before routes that read `req.body`.
2. Register 4-argument error handlers (`err, req, res, next`) LAST, after routes.

### Express CORS

**Fix:**
1. Use the `cors` middleware before routes that need it.
2. Use specific origins in production (not wildcard).
3. For credentialed requests, set `credentials: true` and verify `Access-Control-Allow-Origin` and `Access-Control-Allow-Credentials` headers.

### Nodemon not restarting

**Fix:**
1. Check `nodemon.json` ignore/watch patterns.
2. Verify the changed file is within watched paths.
3. Check filesystem watcher limits (`fs.inotify.max_user_watches`).
4. Restart manually with `rs` in the Nodemon terminal.

### Common Node.js error codes

| Code | Name | Fix |
|---|---|---|
| EADDRINUSE | Port already in use | Change port or kill process |
| ECONNREFUSED | Connection refused | Verify target service running, check host/port |
| ENOTFOUND | DNS lookup failed | Check domain, DNS config, firewall |
| ETIMEDOUT | Connection timed out | Check network, provider status, increase timeout |
| EPERM | Permission denied | Check file permissions, run with correct user |
| EACCES | Permission denied | Check file/dir permissions |
| ENOENT | No such file or directory | Verify path, check file exists |
| EISDIR | Is a directory | Use fs.readFileSync for files, not directories |
| EMFILE | Too many open files | Increase limit, close handles, fix leaks |

---

## 5. FastAPI-Specific Errors

### `ModuleNotFoundError` (FastAPI)

**Fix:**
1. Run from the project root.
2. Verify `app/main.py` (or entry module) exists.
3. Check the module path matches your project structure (e.g., `app.main:app`).
4. Verify Python environment has FastAPI installed: `pip list | grep fastapi`.

### FastAPI CORS

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

**Production:** Use specific origins, not `"*"`. Credentialed requests cannot use wildcard origins.

### FastAPI `422 Unprocessable Entity`

**Cause:** Request body doesn't match the Pydantic schema.

**Fix:**
1. Check field types (string, int, float, bool, list, etc.).
2. Verify required fields are present.
3. Check `Content-Type: application/json` header.
4. Use `/docs` or `/redoc` to test requests interactively.

### FastAPI dependency injection

**Fix:**
1. Use `Depends()` for shared dependencies (DB sessions, auth).
2. Use `yield` with cleanup code after it (e.g., close DB session).
3. Dependencies are cached within one request by default.

### FastAPI background work

**Fix:**
1. Use `BackgroundTasks` for fire-and-forget work after response.
2. Use Celery, RQ, or a message queue for heavy, retryable, long-running, or distributed jobs.

### FastAPI async vs sync endpoints

**Fix:**
1. `def` runs in a threadpool; `async def` runs on the event loop.
2. Never call blocking I/O inside `async def`.
3. Use async-compatible clients (`httpx.AsyncClient`, `asyncpg`).
4. Offload blocking work to a threadpool.

### FastAPI path and query parameters

**Fix:**
1. Path params are part of the URL and required: `@app.get("/items/{item_id}")`.
2. Query params follow `?` and may have defaults.
3. Use `Path()` or `Query()` for validation (length, bounds, regex).

### FastAPI WebSocket

**Fix:**
1. Define route: `@app.websocket("/ws")`.
2. Accept connection: `await websocket.accept()`.
3. Handle disconnects: catch `WebSocketDisconnect`.
4. Check proxy config for WebSocket upgrade headers.

### FastAPI error handling

**Fix:**
1. Use `try/except` in routes and return structured JSON errors.
2. Register exception handlers for global error handling.
3. Return consistent error response shape: `{"error": "human-readable message"}`.
4. Log the full exception with traceback (never return it to clients).

### FastAPI health check

**Fix:**
1. Expose `/health` returning 200 on success.
2. Separate liveness checks (process running) from readiness checks (dependencies available).
3. Optionally include dependency status (DB, Redis, queue).

### FastAPI common error codes

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

---

## 6. Deployment, DevOps, and Infrastructure

### Deployment checklist

1. Set env vars on the platform (never commit secrets).
2. Use a production server (gunicorn/uvicorn workers for Python, node cluster for Node).
3. Disable debug mode in production.
4. Set CORS origins to specific values.
5. Run database migrations before starting.
6. Expose a health check endpoint (`/health`).
7. Monitor logs for startup errors.

### Health checks

**Fix:**
1. Expose `/health` returning 200 on success.
2. Separate liveness checks (process running) from readiness checks (dependencies available).
3. For readiness, optionally verify critical dependencies (DB, Redis, queue).
4. Use short timeouts so the app doesn't block on slow dependencies.

### Rate limiting

**Fix:**
1. Use `slowapi` (Python/FastAPI) or `express-rate-limit` (Node.js).
2. Key by IP or authenticated user.
3. Return `429 Too Many Requests` with a `Retry-After` header.
4. Configure per-user or per-IP limits based on your threat model.

### Memory leaks

**Fix:**
1. Profile with `memory-profiler` (Python) or heap snapshots (Node.js).
2. Common causes: unbounded caches, event listener accumulation, global state.
3. Restart as temporary mitigation.
4. Fix root cause (add size limits, remove listeners, clear caches).

### High CPU usage

**Fix:**
1. Profile with `py-spy` (Python) or `node --prof` (Node.js).
2. Check for infinite loops, blocking operations in async code, excessive regex backtracking.
3. Profile hot functions and optimize.
4. Add rate limiting or worker scaling if CPU is consistently high.

### Port binding / permission denied

**Fix:**
1. Ports below 1024 require root. Use unprivileged ports (8000, 3000, 8080).
2. Use a reverse proxy (nginx, nginx, Caddy) for ports 80/443.
3. "Address already in use" — kill the process or change port.

### Nginx 502 Bad Gateway

**Fix:**
1. Upstream (app) not running or wrong `proxy_pass` port.
2. Check app logs and that the app listens on the expected port.
3. Verify nginx config with `nginx -t`.

### SSL/TLS errors

**Fix:**
1. Certificate expired or mismatched.
2. Renew with `certbot` or cloud provider tool.
3. Ensure full chain is served.
4. For local dev use `mkcert` for a trusted cert.

### Docker container exits immediately

**Fix:**
1. Check logs: `docker logs <container>`.
2. Usually missing CMD, crash on startup, or missing env.
3. Run interactively: `docker run -it image bash` to debug.

### Process management

**Fix:**
1. Use systemd or pm2 for auto-restart.
2. `pm2 start app.js --name api` then `pm2 startup && pm2 save`.
3. Enable on boot for production deployments.

### Redis connection issues

**Fix:**
1. Verify Redis is running: `redis-cli ping` → PONG.
2. Check host/port in connection string.
3. For Docker, use the container name as host.
4. Check authentication credentials if required.

### CI/CD deployment failures

**Fix:**
1. Check deployment logs.
2. Verify env vars set.
3. Check build output.
4. Confirm app reads platform `PORT`.
5. Review health check settings.

### Common infrastructure error codes

| Code | Name | Fix |
|---|---|---|
| 400 | Bad Request | Validate request body |
| 401 | Unauthorized | Provide valid `Authorization: Bearer` header |
| 403 | Forbidden | Check RBAC, API key scope, resource ownership |
| 404 | Not Found | Verify route path and base URL |
| 405 | Method Not Allowed | Configure allowed methods on route |
| 429 | Too Many Requests | Implement exponential backoff with jitter |
| 500 | Internal Server Error | Check backend logs, verify env vars, reproduce |
| 502 | Bad Gateway | Verify backend running, check proxy config |
| 503 | Service Unavailable | Check health endpoint, verify deps, retry with backoff |
| 504 | Gateway Timeout | Review timeout settings, identify slow component |

---

## Safe Troubleshooting Rules

- Record the endpoint, timestamp, HTTP status code, and request ID if available.
- Check the response body and server logs before assuming the cause.
- Never share API keys, admin tokens, passwords, or unredacted secrets.
- Do not expose stack traces or internal implementation details to end users.
- Retry only temporary failures, and use backoff for repeated requests.
- Treat this document as general guidance; confirm exact behaviour against the deployed application.
