# Backend Troubleshooting — Logging, Debugging, Git, Docker, Deployment

This document covers logging, debugging, deployment, and infrastructure issues for any backend type (Python, Node.js, etc.).

---

## Logging errors

**Fix:**
1. Use structured logging with levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
2. Python: `logging` module. Node.js: `winston` or `pino`.
3. Always log exceptions with traceback: `logger.exception("msg")`.
4. Never log secrets or PII (API keys, tokens, passwords, personal data).

---

## Reading stack traces

**Fix:**
1. Read bottom-up. The last frame is where the error originated.
2. Look for your own code frames, not library frames.
3. Check the exception type and message first.
4. Focus on the first relevant frame in your own code.

---

## Debugging with breakpoints

**Fix:**
1. Python: `import pdb; pdb.set_trace()` or `breakpoint()` (Python 3.7+).
2. Node.js: `node --inspect app.js` then Chrome DevTools.
3. VS Code: Set breakpoints and run with debugger attached.
4. Add focused logging at the suspected error location.

---

## Git conflicts

**Fix:**
1. Merge conflict markers: `<<<<<<<`, `=======`, `>>>>>>>`.
2. Resolve by editing, then `git add` and `commit`.
3. Use `git merge --abort` to cancel.
4. For rebase conflicts: `git rebase --continue` or `--abort`.

---

## Git push rejected

**Fix:**
1. Remote has new commits.
2. Run `git pull --rebase` then `git push`.
3. If diverged, resolve conflicts.
4. Never force push to shared branches.

---

## Docker build fails

**Fix:**
1. Check Dockerfile syntax and base image.
2. Build context too large — add `.dockerignore`.
3. Layer caching: order commands from least to most changing.
4. Use multi-stage builds to reduce image size.

---

## Docker networking

**Fix:**
1. Containers on same network resolve by service name.
2. Use `docker network create` for custom networks.
3. Expose ports with `-p host:container`.
4. `localhost` inside a container refers to the container itself, not the host.

---

## Deployment checklist

1. Set env vars on the platform (never commit secrets).
2. Use a production server (gunicorn/uvicorn workers for Python, node cluster for Node).
3. Disable debug mode in production.
4. Set CORS origins to specific values.
5. Run database migrations before starting.
6. Expose a health check endpoint (`/health`).
7. Monitor logs for startup errors.

---

## Health checks

**Fix:**
1. Expose `/health` returning 200 on success.
2. Separate liveness checks (process running) from readiness checks (dependencies available).
3. For readiness, optionally verify critical dependencies (DB, Redis, queue).
4. Use short timeouts so the app doesn't block on slow dependencies.

---

## Rate limiting

**Fix:**
1. Use `slowapi` (Python/FastAPI) or `express-rate-limit` (Node.js).
2. Key by IP or authenticated user.
3. Return `429 Too Many Requests` with a `Retry-After` header.
4. Configure per-user or per-IP limits based on your threat model.

---

## Memory leaks

**Fix:**
1. Profile with `memory-profiler` (Python) or heap snapshots (Node.js).
2. Common causes: unbounded caches, event listener accumulation, global state.
3. Restart as temporary mitigation.
4. Fix root cause (add size limits, remove listeners, clear caches).

---

## High CPU usage

**Fix:**
1. Profile with `py-spy` (Python) or `node --prof` (Node.js).
2. Check for infinite loops, blocking operations in async code, excessive regex backtracking.
3. Profile hot functions and optimize.
4. Add rate limiting or worker scaling if CPU is consistently high.

---

## Port binding / permission denied

**Fix:**
1. Ports below 1024 require root. Use unprivileged ports (8000, 3000, 8080).
2. Use a reverse proxy (nginx, nginx, Caddy) for ports 80/443.
3. "Address already in use" — kill the process or change port.

---

## Nginx 502 Bad Gateway

**Fix:**
1. Upstream (app) not running or wrong `proxy_pass` port.
2. Check app logs and that the app listens on the expected port.
3. Verify nginx config with `nginx -t`.

---

## SSL/TLS errors

**Fix:**
1. Certificate expired or mismatched.
2. Renew with `certbot` or cloud provider tool.
3. Ensure full chain is served.
4. For local dev use `mkcert` for a trusted cert.

---

## Docker container exits immediately

**Fix:**
1. Check logs: `docker logs <container>`.
2. Usually missing CMD, crash on startup, or missing env.
3. Run interactively: `docker run -it image bash` to debug.

---

## Process management

**Fix:**
1. Use systemd or pm2 for auto-restart.
2. `pm2 start app.js --name api` then `pm2 startup && pm2 save`.
3. Enable on boot for production deployments.

---

## Redis connection issues

**Fix:**
1. Verify Redis is running: `redis-cli ping` → PONG.
2. Check host/port in connection string.
3. For Docker, use the container name as host.
4. Check authentication credentials if required.

---

## Common infrastructure error codes

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
