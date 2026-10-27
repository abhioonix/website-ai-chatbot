# Backend Error Codes and Troubleshooting Guide

> **Purpose:** A practical reference for diagnosing common backend authentication, API, Python, FastAPI, Node.js/Express, database, server, Git, Docker, and deployment issues.
>
> **Important:** Not every issue below has a numeric error code. HTTP status codes are standardized response codes; messages such as `ModuleNotFoundError` and `EADDRINUSE` are runtime or operating-system errors.

## Quick Reference: HTTP Status Codes

| Code | Name | What it means | First checks |
|---|---|---|---|
| `400` | Bad Request | The request is invalid or malformed. | Check request syntax, parameters, and JSON formatting. |
| `401` | Unauthorized | Authentication is missing, invalid, or expired. | Check the token, signature, expiry, and authentication header. |
| `403` | Forbidden | The caller is authenticated but lacks permission, or access is otherwise denied. | Check roles, permissions, scopes, and route guards. |
| `404` | Not Found | The requested resource or route cannot be found. | Check the URL, route registration, and resource ID. |
| `409` | Conflict | The request conflicts with the current resource state. | Check duplicate records, version conflicts, and resource state. |
| `422` | Unprocessable Entity | The server cannot process the request data as provided. FastAPI commonly uses this for validation failures. | Compare the request body and parameters with the validation schema. |
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
- The token was signed with a different or incorrect secret/key.
- The server expects a different token format or issuer/audience.
- The server and client clocks differ enough to affect time validation.

**Troubleshooting**
1. Inspect the token's expiry and required claims without exposing the token publicly.
2. Confirm the client sends the expected `Authorization: Bearer <token>` header.
3. Verify the configured signing key, issuer, audience, and algorithm match between token creation and validation.
4. Refresh the token or sign in again if it has expired.
5. Keep secrets in environment variables or a secrets manager; never commit them to source control.

### `403 Forbidden`

**Possible causes:** Missing role, permission, scope, or access policy.

**Troubleshooting:** Check role-based access control (RBAC), token scopes, resource ownership rules, and route guards. Confirm that the user is authenticated but is not being granted access to an action they should be allowed to perform.

### Session expired

**Possible causes:** Session expiry, cookie expiry, server-side session timeout, or a missing session cookie.

**Troubleshooting:** Check server-side session settings and cookie `Max-Age`/`Expires` values. Ensure the client sends the cookie. Extend the lifetime only if appropriate for the application's security requirements; otherwise, prompt the user to sign in again.

---

## 2. Database and Server Issues

### Database connection refused

**Possible causes:** The database service is stopped, the host or port is wrong, a network rule blocks access, or the application is using the wrong connection string.

**Troubleshooting**
1. Check that the database is running and listening on the expected host/port.
2. Verify the database name, host, port, username, password, and TLS options in the connection configuration.
3. Check firewall rules and container/network configuration.
4. For Docker Compose, use the database **service name** as the host when connecting from another container. `localhost` inside a container refers to that same container, not another container.
5. On a system using systemd, a PostgreSQL service can often be checked with `systemctl status postgresql` (service names vary by installation).

### Database authentication failed

**Possible causes:** Incorrect credentials, connecting to the wrong database, or insufficient database privileges.

**Troubleshooting:** Verify the environment variables and confirm that the database user has only the permissions required by the application. Grant syntax differs across database engines; use the correct syntax for PostgreSQL, MySQL, or the database in use. Do not copy a MySQL-specific `GRANT` command into PostgreSQL.

### Connection pool exhausted

**Possible causes:** Too many concurrent requests, sessions/connections not being closed, or a pool limit that is too small for the workload.

**Troubleshooting**
- Review pool size, overflow, timeout, and database connection limits for the ORM/driver in use (for example, SQLAlchemy or Prisma).
- Close sessions and connections reliably, including on exceptions. Use context managers or framework dependency cleanup where supported.
- Look for leaked connections and long-running queries before simply increasing the pool size.

### Database migration or schema-drift errors

**Possible causes:** The database schema differs from the migration history, migrations conflict, or a migration was changed after being applied.

**Troubleshooting**
- Read the migration tool's output and compare the current schema with migration history.
- With Alembic, review an autogenerated revision before applying it, then use `alembic upgrade head` when the migration is correct.
- For genuinely conflicting migration branches, create a merge migration using the tool's documented workflow.
- Avoid editing migrations that have already been applied in shared or production environments. Create a new corrective migration instead.

### Port binding errors: `EADDRINUSE` / “Address already in use”

**Possible causes:** Another process is already listening on the requested port.

**Troubleshooting**
- Choose another port or stop the process that owns the port, after verifying it is safe to stop.
- Linux/macOS example: `lsof -i :3000`
- Windows example: `netstat -ano | findstr :3000`
- Configure the port consistently through the application's `PORT` setting and the deployment/proxy configuration.

### “Permission denied” when binding a port

On many Unix-like systems, ports below `1024` require elevated privileges. Prefer an unprivileged application port such as `8000` or `3000` and put a reverse proxy such as Nginx in front of it rather than running the application as root.

### `500 Internal Server Error`

**Possible causes:** An unhandled exception, missing environment variable, failed database operation, or another unexpected backend failure.

**Troubleshooting**
1. Check application logs and the full traceback around the failed request.
2. Reproduce the issue with the same request and environment.
3. Verify environment variables and upstream services.
4. Log useful diagnostic details while avoiding credentials, tokens, and personal data.
5. Enable detailed debug output only in a controlled development environment; do not expose debug tracebacks to production users.

### Nginx `502 Bad Gateway`

**Possible causes:** The upstream application is stopped, the upstream port/socket is wrong, or the proxy cannot reach the application.

**Troubleshooting:** Check application logs and listening ports, verify Nginx's `proxy_pass`/upstream settings, and validate the Nginx configuration with `nginx -t` before reloading it.

### `504 Gateway Timeout`

**Possible causes:** The upstream service takes too long to respond, a query is slow, or a timeout is too short.

**Troubleshooting:** Check upstream health, database query plans, external API calls, application logs, and proxy/application timeout settings. Fix the underlying latency before increasing timeouts indiscriminately.

### SSL/TLS errors

**Possible causes:** An expired certificate, a hostname mismatch, an incomplete certificate chain, an untrusted certificate, or incorrect client/server TLS settings.

**Troubleshooting:** Verify certificate validity and hostname, serve the required certificate chain, and renew certificates using the relevant certificate-management process (for example, Certbot when applicable). For local development, use a trusted local development certificate. Avoid disabling certificate verification as a permanent workaround.

### Docker container exits immediately

**Possible causes:** The application crashes during startup, required environment variables are missing, the image has an incorrect command, or the container's main process finishes.

**Troubleshooting**
- Read logs: `docker logs <container>`
- Inspect state and exit code: `docker ps -a` and `docker inspect <container>`
- Verify the image's `CMD`/entrypoint, configuration, dependencies, and environment.
- For interactive diagnosis, use a suitable shell available in the image; not every image contains `bash`.

### Process management

Use a process manager or deployment platform appropriate for the environment. For example, PM2 can manage a Node.js process with `pm2 start app.js --name api`, and its startup instructions can be configured with `pm2 startup` followed by `pm2 save`. Review the commands and permissions for your operating system before enabling startup on boot.

---

## 3. FastAPI Troubleshooting

### `uvicorn app.main:app` fails with “Could not import module”

**Possible causes:** The command is running from the wrong directory, the module path is wrong, or the application object has a different name.

**Troubleshooting:** Run the command from the project root and confirm that `app/main.py` exists and defines an object named `app`. The target `app.main:app` means **module** `app.main`, **object** `app`. Adjust the import target if your structure differs.

### CORS errors in the browser

CORS is enforced by the browser. Configure `CORSMiddleware` with the frontend's exact origin(s). Do not use a wildcard origin when sending credentialed requests.

Example for development (replace the origin with the frontend's actual origin):

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Use an explicit allowlist in production. The frontend must also send credentials when cookies or other browser credentials are required.

### `422 Unprocessable Entity`

**Likely cause:** The request's body, path, or query parameters do not match FastAPI/Pydantic validation requirements.

**Troubleshooting:** Read the response's validation details, check required fields and types, confirm JSON requests use `Content-Type: application/json`, and test the request through `/docs`. Ensure the client sends the expected structure rather than a string or form body when JSON is required.

### Dependency injection and cleanup

Use `Depends()` for shared dependencies such as authentication and database sessions. For resources that must be cleaned up, use a dependency with `yield` and close/release the resource in its cleanup path. Dependencies are generally cached within one request by default unless configured otherwise.

### Background work

Use FastAPI `BackgroundTasks` for small tasks that can run after the response is returned. Use a task queue such as Celery or RQ for heavy, retryable, long-running, or distributed jobs.

### Async versus sync endpoints

FastAPI runs a normal `def` path operation in a threadpool; `async def` runs on the event loop. Do not call blocking operations such as `time.sleep()` or blocking network I/O directly inside `async def`. Use async-compatible clients (for example, `httpx.AsyncClient`) or offload blocking work appropriately.

### Path and query parameters

Path parameters are part of the URL and are generally required. Query parameters follow `?` and may have defaults. Use FastAPI's `Path()` or `Query()` validators where appropriate (for example, length limits and numeric bounds); validation options depend on the parameter type and installed FastAPI/Pydantic version.

### WebSocket issues

Define a WebSocket route with `@app.websocket("/ws")`, accept the connection with `await websocket.accept()`, and handle client disconnects (for example, using `WebSocketDisconnect`). Check proxy configuration and network support if WebSocket connections fail only after deployment.

---

## 4. Python Troubleshooting

### `ModuleNotFoundError`

**Possible causes:** A package is not installed, the wrong Python interpreter or virtual environment is active, the working directory/module path is wrong, or a package layout/import path is incorrect.

**Troubleshooting**
1. Activate the project's virtual environment.
2. Install project dependencies: `python -m pip install -r requirements.txt`
3. Confirm which interpreter is running: `python --version` and `python -m pip --version`.
4. Run the command from the project root and verify the import path and package layout. An `__init__.py` may be needed for some package layouts, though namespace packages can work without one.

### `ImportError: cannot import name ...`

**Possible causes:** A misspelled or missing symbol, the wrong module being imported, or a circular import.

**Troubleshooting:** Check spelling and the source module, confirm which file Python is loading, and simplify circular dependencies. Moving an import inside a function can sometimes help, but prefer reorganizing shared code so modules do not depend on each other cyclically.

### Create and activate a virtual environment

Create one from the project directory:

```bash
python -m venv .venv
```

Activate it:

```bash
# Linux/macOS
source .venv/bin/activate

# Windows Command Prompt
.venv\Scripts\activate.bat

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Deactivate it with `deactivate`. Install dependencies inside the active environment and use `python -m pip` to ensure pip belongs to that interpreter.

### `pip install` fails

**Troubleshooting:** Upgrade pip with `python -m pip install --upgrade pip`, confirm the Python version is supported by the package, and read the first meaningful error in the build output. Native packages may require compiler/build tools appropriate for the operating system. For SSL errors, fix the certificate/proxy configuration; do not bypass TLS verification unless a trusted administrator has provided a narrowly scoped, temporary development procedure.

### Asyncio event-loop errors

Messages such as “Event loop is closed” or “cannot run nested event loop” can indicate incorrect event-loop management.

**Troubleshooting:** Do not call `asyncio.run()` from inside an already running event loop. Use `await` inside async functions. From ordinary synchronous top-level code, `asyncio.run()` can be used once to run the main coroutine.

### Type errors and tracebacks

Read the exception type and message, then inspect the traceback frames to locate the line in your code that triggered the problem. Check for `None`, unexpected types, missing dictionary keys, and invalid assumptions about input. Use targeted logging, a debugger, or `breakpoint()` to inspect values.

### Environment variables in Python

Use `os.getenv("NAME")` for optional values and validate required configuration during startup. Use `python-dotenv` for local `.env` files if needed. `os.environ.setdefault()` does not replace a value that is already set. Never commit secrets or production credentials to source control.

### Python logging

Prefer the `logging` module to scattered `print()` calls. A simple setup is:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

Use `logger.exception("Description of failure")` inside an exception handler to include the traceback. Avoid logging passwords, tokens, or personal data.

---

## 5. Node.js and Express Troubleshooting

### `npm install` fails

**Possible causes:** Dependency conflicts, unsupported Node.js version, registry/network problems, or native dependencies that cannot build.

**Troubleshooting:** Check the Node.js version and the package's `engines` requirements, review the first actionable npm error, and confirm registry/network access. For a project with a committed lockfile, `npm ci` is often a reproducible way to install dependencies. Clear the npm cache only when there is evidence of cache corruption; avoid deleting the lockfile as a first step because it can change dependency versions. Use a version manager such as `nvm` when the project requires another Node.js version.

### `EADDRINUSE: address already in use`

**Cause:** Another process is listening on the configured port.

**Troubleshooting:** Identify the process with `lsof -i :3000` on Linux/macOS or `netstat -ano | findstr :3000` on Windows. Stop it only after confirming it is safe, or configure a different port using the `PORT` environment variable.

### `Cannot find module`

**Possible causes:** A dependency is not installed, a local path is wrong, or CommonJS/ES-module settings do not match the code.

**Troubleshooting:** Run the appropriate install command, verify local imports use paths such as `./utils.js` where required, and check `package.json` module configuration. For ES modules, set `"type": "module"` in `package.json`; follow the runtime's module rules consistently.

### Express middleware order

Middleware executes in registration order. Register parsers such as `express.json()` before routes that read `req.body`. Register not-found handling after application routes and error-handling middleware (with the `(err, req, res, next)` signature) after the routes/middleware whose errors it handles.

### CORS in Express

Install/configure the `cors` middleware before the routes that need it. Example for a local frontend:

```javascript
const cors = require("cors");
app.use(cors({
  origin: "http://localhost:3000",
  credentials: true,
}));
```

Use the real frontend origin(s) in production. Credentialed requests cannot use `Access-Control-Allow-Origin: *`. The browser client must also be configured to send credentials where required.

### Unhandled promise rejection / async route errors

Handle rejected promises from asynchronous code. Use `try/catch` and pass failures to Express error middleware, or use a wrapper compatible with the version of Express in use. Runtime behavior for unhandled rejections depends on the Node.js version and runtime settings; do not rely on unhandled rejections as an error-handling strategy.

### Environment variables in Node.js

Read configuration with `process.env.NAME`. For a local `.env` file, use a library such as `dotenv` when appropriate. Validate required values at startup and never commit `.env` files or secrets. In CommonJS, a common pattern is `require("dotenv").config()`; ES modules use their corresponding import syntax.

### Nodemon does not restart

Check `nodemon.json` and ignore/watch patterns, confirm the changed file is within the watched paths, and check filesystem watcher limits where relevant. You can type `rs` in the Nodemon terminal to restart manually.

### `EPERM` or symlink errors on external drives

Some filesystems and mount configurations have limited symlink or permission support. Check the exact error and filesystem mount options. If the project cannot reliably install dependencies on the external drive, move it to a supported local filesystem and retry rather than applying broad permission changes.

---

## 6. Application Logs and Debugging

### Reading stack traces

1. Read the exception/error type and message first.
2. Follow the traceback frames to the line of code that raised the error; in Python, the final line typically states the exception, while the frames show the call path.
3. Look for the first relevant frame in your own code and inspect the values passed into it.
4. Reproduce with a small, known input and add focused logging or a breakpoint.

A stack trace does not always mean the last displayed source frame is in your own code; use the exception message and call path together.

### Useful debugging tools

- **Python:** `breakpoint()` or `import pdb; pdb.set_trace()`; VS Code debugger.
- **Node.js:** `node --inspect app.js` and inspect with Chrome DevTools or a supported IDE debugger.
- **Logs:** Use severity levels such as `DEBUG`, `INFO`, `WARNING`, `ERROR`, and `CRITICAL`.

Use structured logging where possible. In Python, `logging` is built in; in Node.js, libraries such as Winston or Pino can help. Log exceptions with tracebacks where appropriate, but never log passwords, authentication tokens, API keys, or unnecessary personal data.

---

## 7. Git Issues

### Merge conflicts

Git marks conflicted areas with markers such as `<<<<<<<`, `=======`, and `>>>>>>>`.

**Resolution:** Edit the file to keep the intended content and remove the conflict markers, run tests, then stage the resolved file with `git add <file>` and complete the merge commit if Git requires one. To cancel a merge in progress, use `git merge --abort`. For a rebase conflict, resolve and stage files, then use `git rebase --continue`; use `git rebase --abort` to cancel the rebase.

### `git push` rejected

**Common cause:** The remote branch has commits not present locally, or the branch has a policy/permission restriction.

**Troubleshooting:** Read Git's rejection message first. When the history can be safely rebased, use `git pull --rebase`, resolve conflicts, run tests, then push. Check branch permissions and protection rules if the rejection is not due to diverged history. Avoid force-pushing to shared branches; it can overwrite other contributors' work.

---

## 8. Docker and Deployment

### Docker build fails

**Troubleshooting:** Check Dockerfile syntax, the base image, dependency installation, and build logs. Add a `.dockerignore` file to exclude unneeded files such as local virtual environments, `node_modules`, caches, and secrets from the build context. Order Dockerfile steps to make sensible use of layer caching. Consider multi-stage builds when they simplify or reduce the final image.

### Docker networking problems

- Containers on the same user-defined Docker network can typically reach one another by container/service name.
- Inside a container, `localhost` refers to that container itself.
- Publish ports with `-p host_port:container_port` when host access is needed.
- Confirm services listen on the expected interface and port and that the required network exists.

### Deployment checklist

- Configure required environment variables and secrets on the deployment platform.
- Use an appropriate production server/process configuration (for example, Uvicorn workers or Gunicorn for supported Python deployments).
- Disable debug mode and avoid exposing stack traces publicly.
- Restrict CORS origins and configure cookies/TLS correctly.
- Apply database migrations through the deployment process.
- Add a health endpoint and monitor application/error logs.
- Verify startup, connectivity, permissions, and rollback procedures.

### Health checks

Provide an endpoint such as `/health` that returns HTTP `200` when the service is healthy. Use liveness and readiness checks appropriately in containers/orchestrators. A deeper readiness check can verify database connectivity, but avoid making a liveness probe depend on a downstream service if that could cause unnecessary restart loops.

### Rate limiting: `429 Too Many Requests`

Use a rate-limiting mechanism suitable for the framework (for example, SlowAPI in FastAPI or `express-rate-limit` in Express). Choose keys and limits according to the threat model, such as IP address or authenticated user, and return `429` when a client exceeds its allowed rate. Include `Retry-After` when appropriate. Configure trusted proxy handling carefully so client IPs cannot be spoofed.

---

## 9. Performance and Reliability

### Memory leaks

**Common causes:** Unbounded caches, retained references, accumulating event listeners, or uncontrolled global state.

**Troubleshooting:** Profile memory over time. Python options include `memory-profiler`; Node.js can use heap snapshots and built-in profiling tools. Restarting may be a temporary mitigation, but identify and fix the root cause.

### High CPU usage

**Common causes:** Infinite loops, excessive computation, blocking operations inside async code, or pathological regular expressions.

**Troubleshooting:** Profile before optimizing. Tools include `py-spy` for Python and `node --prof` for Node.js. Inspect hot functions, loop conditions, synchronous work, and unexpectedly expensive regular expressions.

### Slow database queries

**Troubleshooting:** Use `EXPLAIN` or, where appropriate, `EXPLAIN ANALYZE` to understand query plans. Consider indexes on frequently filtered/joined columns, avoid N+1 query patterns (for example, with eager loading), limit the result set, and paginate large responses. `EXPLAIN ANALYZE` may execute the query, so use care with expensive or mutating statements and production workloads.

### API versioning

Use a consistent strategy, such as a path prefix (`/api/v1`). Document supported versions and deprecation timelines, and give clients time to migrate before removing an older version. Header-based versioning is also possible; consistency and documentation matter more than the specific strategy.

---

## 10. General Troubleshooting Checklist

When an issue occurs, collect enough information to diagnose it without exposing secrets:

1. **Reproduce:** Record the endpoint/command, sanitized input, expected result, and actual result.
2. **Classify:** Determine whether it is an HTTP response code, application exception, dependency/tool error, network failure, or configuration problem.
3. **Read logs:** Check the relevant application, proxy, database, and container logs around the failure time.
4. **Verify configuration:** Check hostnames, ports, environment variables, dependency versions, permissions, and active virtual environments.
5. **Check recent changes:** Review recent code, dependency, schema, configuration, and deployment changes.
6. **Test the fix:** Reproduce the original case and run relevant regression tests.
7. **Document:** Record the symptom, root cause, fix, and any prevention steps.

### LLM: chatbot_gives_no_knowledge_based_answer
**Fix:**
1. Call `GET /kb/status`.
2. Confirm `enabled` is `true`.
3. Confirm embedding/vector-store config is present.
4. Confirm source documents are in `knowledge_base/`.
5. Rebuild the index after adding or changing documents.

---

## Suggested Issue Record Template

Use this template to document a newly discovered project-specific error:

```markdown
### [Error title or code]

- **Category:** Authentication / API / Database / Runtime / Deployment / Other
- **Symptom:** What the user or logs show
- **Cause:** Confirmed root cause, or the most likely cause if not yet confirmed
- **Resolution:** Steps taken to fix the issue
- **Prevention:** Test, alert, configuration check, or process that may prevent recurrence
- **References:** Relevant logs, issue link, or documentation (remove secrets and personal data)
```

---

**Security reminder:** Never paste real passwords, JWTs, API keys, private certificates, session cookies, or personal data into this file or into shared logs. Replace them with placeholders before sharing diagnostic information.
