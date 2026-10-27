# Backend Troubleshooting — Logging, Debugging, Git, Docker, Deployment

## Logging errors

Use structured logging with levels: DEBUG, INFO, WARNING, ERROR, CRITICAL. In Python use logging module; in Node use winston or pino. Always log exceptions with traceback: logger.exception("msg"). Don't log secrets or PII.

## Reading stack traces

Read bottom-up. The last frame is where the error originated. Look for your own code frames, not library frames. Check the exception type and message first.

## Debugging with breakpoints

Python: import pdb; pdb.set_trace() or use breakpoint() (3.7+). VS Code: set breakpoints and run with debugger. Node: node --inspect app.js then Chrome DevTools.

## Git conflicts

Merge conflict markers: <<<<<<<, =======, >>>>>>>. Resolve by editing, then git add and commit. Use git merge --abort to cancel. For rebase conflicts: git rebase --continue or --abort.

## Git push rejected

Remote has new commits. Run git pull --rebase then push. If diverged, resolve conflicts. Never force push to shared branches.

## Docker build fails

Check Dockerfile syntax and base image. Build context too large — add .dockerignore. Layer caching: order commands from least to most changing. Use multi-stage builds to reduce image size.

## Docker networking

Containers on same network resolve by service name. Use docker network create. Expose ports with -p host:container. localhost inside container refers to container itself, not host.

## Deployment checklist

Set env vars on platform. Use production WSGI server (gunicorn/uvicorn workers). Disable debug mode. Set CORS origins. Run migrations. Health check endpoint. Monitor logs.

## Health checks

Expose /health returning 200. Use for load balancer and container orchestrator probes. Include DB connectivity check for deep health.

## Rate limiting

Use slowapi (FastAPI) or express-rate-limit. Key by IP or user. Return 429 Too Many Requests. Add Retry-After header.

## Memory leaks

Profile with memory-profiler (Python) or heap snapshots (Node). Common causes: unbounded caches, event listener accumulation, global state. Restart as mitigation, fix root cause.

## High CPU usage

Profile with py-spy or node --prof. Check for infinite loops, sync blocking in async code, excessive regex backtracking.

## Database slow queries

Use EXPLAIN/EXPLAIN ANALYZE. Add indexes on filtered/joined columns. Avoid N+1 queries (use eager loading). Paginate large results.

## API versioning

Prefix routes with /api/v1. Keep old versions until clients migrate. Use header or path versioning consistently.

---

## Additional Operations / DevOps Errors

### Structured logging and log levels
**Fix:** Use `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` levels. Python: `logging` module. Node: `winston` or `pino`. Always log exceptions with traceback: `logger.exception("msg")`. Never log secrets or PII.

### Reading stack traces
**Fix:** Read bottom-up. The last frame is where the error originated. Look for your own code frames, not library frames. Check the exception type and message first.

### Debugging with breakpoints
**Fix:** Python: `import pdb; pdb.set_trace()` or `breakpoint()` (3.7+). VS Code: set breakpoints and run with debugger. Node: `node --inspect app.js` then Chrome DevTools.

### Git conflicts
**Fix:** Merge conflict markers: `<<<<<<<`, `=======`, `>>>>>>>`. Resolve by editing, then `git add` and `commit`. Use `git merge --abort` to cancel. For rebase conflicts: `git rebase --continue` or `--abort`.

### Git push rejected
**Fix:** Remote has new commits. Run `git pull --rebase` then `push`. If diverged, resolve conflicts. Never force push to shared branches.

### Docker build fails
**Fix:** Check Dockerfile syntax and base image. Build context too large — add `.dockerignore`. Layer caching: order commands from least to most changing. Use multi-stage builds to reduce image size.

### Docker networking
**Fix:** Containers on same network resolve by service name. Use `docker network create`. Expose ports with `-p host:container`. `localhost` inside container refers to container itself, not host.

### Deployment checklist
**Fix:** Set env vars on platform. Use production server (gunicorn/uvicorn workers). Disable debug mode. Set CORS origins. Run migrations. Health check endpoint. Monitor logs.

### Health checks
**Fix:** Expose `/health` returning 200. Use for load balancer and container orchestrator probes. Include DB connectivity check for deep health. Separate liveness from readiness checks.

### Rate limiting
**Fix:** Use `slowapi` (FastAPI) or `express-rate-limit`. Key by IP or user. Return `429 Too Many Requests`. Add `Retry-After` header.

### Memory leaks
**Fix:** Profile with `memory-profiler` (Python) or heap snapshots (Node). Common causes: unbounded caches, event listener accumulation, global state. Restart as mitigation, fix root cause.

### High CPU usage
**Fix:** Profile with `py-spy` or `node --prof`. Check for infinite loops, sync blocking in async code, excessive regex backtracking.

### Port binding / permission denied
**Fix:** Ports below 1024 require root. Use 8000/3000 or run behind nginx. "Address already in use" — kill the process or change port.

### Nginx 502 Bad Gateway
**Fix:** Upstream (app) not running or wrong `proxy_pass` port. Check app logs and that the app listens on the expected port. Verify nginx config with `nginx -t`.

### SSL/TLS errors
**Fix:** Certificate expired or mismatched. Renew with certbot. Ensure full chain is served. For local dev use `mkcert`.

### Docker container exits immediately
**Fix:** Check logs: `docker logs <container>`. Usually missing CMD, crash on startup, or missing env. Run interactively: `docker run -it image bash`.

### Process management
**Fix:** Use systemd or pm2 for auto-restart. `pm2 start app.js --name api`. Enable on boot: `pm2 startup && pm2 save`.

### Redis connection issues
**Fix:** Verify Redis is running (`redis-cli ping`). Check host/port in connection string. For Docker, use the container name as host. Check authentication credentials if required.

### Elasticsearch/MongoDB errors
**Fix:** MongoDB: check replica set config, verify connection string with credentials, ensure network access is allowed. Elasticsearch: verify cluster health, check shard allocation, review index mappings and mappings conflicts.

### Git cherry-pick / rebase conflicts
**Fix:** For rebase: `git rebase --continue` or `--abort`. For merge: `git merge --abort`. Resolve conflict markers, stage resolved files, commit or abort as appropriate.

### Deployment to Render
**Fix:** Set env vars on platform, use production server/process config, disable debug, restrict CORS origins, configure cookies/TLS correctly, apply DB migrations, add health endpoint, monitor logs.
