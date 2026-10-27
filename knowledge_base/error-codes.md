# Backend Error Codes — Comprehensive Reference

## Purpose

This document is a consolidated reference for backend error codes across categories: HTTP status codes, network/protocol, server/OS, database/storage, queue/worker, AI/LLM/provider, cloud (AWS/GCP/Azure), mobile/web, and infrastructure/security. It complements `backend-http.md` (HTTP status codes) and `backend-ops.md` (deployment/DevOps).

Use this as the single source of truth for error-code troubleshooting. Categorize any error into one of the sections below.

---

## 1. HTTP Status Codes and API Errors

### 400 — Bad Request
**Meaning:** The server cannot process the request because the request data is invalid or malformed.
**Common causes:** JSON body malformed, missing required field, wrong data type, unsupported request format.
**How to troubleshoot:** Validate JSON, confirm `message` is a string, check `history` format, read the error message and correct the request.

### 401 — Unauthorized
**Meaning:** Authentication required but missing, invalid, or expired.
**Common causes:** Protected endpoint requires token, admin token missing/incorrect, env var not configured.
**How to troubleshoot:** Check auth requirement, verify `KB_ADMIN_TOKEN` for rebuild, send `x-kb-admin-token` header, never commit tokens to Git.

### 403 — Forbidden
**Meaning:** Server understood request but refuses to allow it.
**Common causes:** Valid credentials but no permission, hosting/security rule, proxy/platform policy.
**How to troubleshoot:** Check RBAC, scopes, route guards, security logs. Do not disable security controls as a first fix.

### 404 — Not Found
**Meaning:** Requested route or resource does not exist.
**Common causes:** URL/route path misspelled, wrong backend base URL, stale deployment, wrong host/path.
**How to troubleshoot:** Verify base URL and route path, check documented routes (`/health`, `/widget.js`, `/kb/status`, `/kb/rebuild`, `/api/chat`), check deployment logs.

### 405 — Method Not Allowed
**Meaning:** URL exists but endpoint does not support the HTTP method used.
**Fix:** Check client method (GET/POST/PUT/PATCH/DELETE), configure allowed methods on route, return proper `Allow` header.

### 406 — Not Acceptable
**Meaning:** Server cannot return a response in any format listed in the request's Accept header.
**Fix:** Check client Accept header and supported response formats.

### 408 — Request Timeout
**Meaning:** The request took too long and timed out.
**Common causes:** Slow network, busy backend, upstream AI provider slow.
**How to troubleshoot:** Retry once after checking network, check backend logs, review `LLM_TIMEOUT_SECONDS` (default 30s), avoid rapid retries.

### 409 — Conflict
**Meaning:** Request conflicts with current resource state (e.g., duplicate record).
**Fix:** Check for duplicate records, use unique constraints, return clear conflict message, consider optimistic locking for concurrent updates.

### 410 — Gone
**Meaning:** Resource intentionally removed and no longer available.
**Fix:** Confirm retirement, update clients to replacement route, document deprecation.

### 413 — Payload Too Large
**Meaning:** Request body exceeds server/intermediary limit.
**Common causes:** Unusually large request, long chat history, proxy/platform limit.
**How to troubleshoot:** Reduce body size, send only needed history, check server/proxy limits, ensure request below 10 MB guard.

### 415 — Unsupported Media Type
**Meaning:** Content-Type not supported by the endpoint.
**Fix:** Send expected content type (e.g., `application/json`), verify parser/upload handler enabled.

### 416 — Range Not Satisfiable
**Meaning:** Requested byte range outside available content.
**Fix:** Check Range header, current file size, handle consistently.

### 424 — Failed Dependency
**Meaning:** Request failed because a dependent operation failed.
**Fix:** Inspect downstream service, return useful error, retry only for transient failures.

### 429 — Too Many Requests
**Meaning:** Client exceeded rate limit.
**Common causes:** Tight loop, shared rate limit, provider applies rate limiting.
**How to troubleshoot:** Wait, check `Retry-After`, prevent duplicate submissions, review rate limits, use exponential backoff.

### 500 — Internal Server Error
**Meaning:** Unexpected server-side failure.
**Common causes:** Unhandled exception, missing config, DB failure, dependency error.
**How to troubleshoot:** Check backend logs, verify env vars, reproduce with same request/body, check recent changes, never expose secrets/stack traces.

### 502 — Bad Gateway
**Meaning:** Gateway/proxy received invalid response from backend/upstream.
**Common causes:** Backend down/restarting, wrong proxy port, upstream crash.
**How to troubleshoot:** Verify backend running, test `GET /health`, review logs, verify upstream address/port, check if backend host or external provider caused it.

### 503 — Service Unavailable
**Meaning:** Service temporarily unable to handle requests.
**Common causes:** Restarting/overloaded/suspended, upstream dependency down, service not ready.
**How to troubleshoot:** Check service status, call `GET /health` and inspect reported status, verify LLM/KB config, review logs, retry after delay with backoff.

### 504 — Gateway Timeout
**Meaning:** Gateway/proxy did not receive response from backend/upstream in time.
**Common causes:** AI-provider slow, backend waiting on network call, short proxy timeout.
**How to troubleshoot:** Check backend logs, review timeouts, check AI provider status, retry safely after delay, identify the slow component first.

### WebSocket Issues
**Cause:** WebSocket route not working or disconnects.
**Fix:** Define route with `@app.websocket("/ws")`, accept with `await websocket.accept()`, handle `WebSocketDisconnect`, check proxy config.

---

## 2. Network and Protocol Errors

### DNS resolution failed / "Name or service not known"
**Meaning:** Hostname could not be resolved to an IP.
**Fix:** Test `nslookup <host>` or `dig <host>`, verify domain is correct and active, check DNS server config (`/etc/resolv.conf`), test with another DNS server (8.8.8.8, 1.1.1.1).

### NXDOMAIN / "Non-Existent Domain"
**Meaning:** Domain does not exist in DNS.
**Fix:** Verify domain and record type with registrar, add missing A/AAAA record, fix CNAME chains, wait for DNS propagation.

### DNS timeout
**Meaning:** DNS server took too long to respond.
**Fix:** Try another DNS server, check firewall (UDP/TCP 53), verify DNS server reachable, increase client timeout.

### Connection timed out (TCP-level)
**Meaning:** TCP connection to host did not complete within timeout.
**Fix:** Test `nc -zv <host> <port>`, verify host is running, check firewall rules, check routing (`traceroute`, `mtr`), verify port is not blocked by cloud security group.

### Connection reset (TCP-level)
**Meaning:** Remote end closed connection abruptly.
**Fix:** Check receiving service logs, verify service is healthy, check memory/CPU limits, verify service listens on expected interface/port.

### Connection refused (TCP-level)
**Meaning:** Remote end actively refused connection (nothing listening on that port).
**Fix:** Verify service is running, check listening address (`ss -tlnp`), for Docker use container/service name as host, verify connection string.

### HTTP/2 PROTOCOL_ERROR
**Meaning:** HTTP/2 frame malformed or stream in invalid state.
**Fix:** Verify server HTTP/2 support, check middleware/proxy that may strip HTTP/2, test HTTP/1.1 to rule out issue, update server.

### HTTP/2 FLOW_CONTROL_ERROR
**Meaning:** Sender exceeded flow-control window.
**Fix:** Fix receiver to drain window, reduce sender data rate/batch size, restart stream/connection if needed.

### HTTP/3 / QUIC errors
**Meaning:** QUIC/HTTP/3 connection failed.
**Fix:** Verify server HTTP/3 enabled, check UDP is not blocked (`nc -vz -u <host> 443`), verify ALPN includes `h3`, test with HTTP/2 fallback.

### SSL handshake failed
**Meaning:** TLS handshake did not complete.
**Fix:** Verify certificate valid/not expired, check TLS version/cipher support, provide full cert chain, if server requires client cert verify it, test with `openssl s_client`.

### CERTIFICATE_VERIFY_FAILED
**Meaning:** Peer certificate could not be verified.
**Fix:** Install CA cert/trust store, provide full cert chain, check system clock, verify revocation status (OCSP/CRL).

### DEPTH_ZERO_SELF_SIGNED_CERT
**Meaning:** Self-signed cert with no trusted CA provided.
**Fix:** For dev use `mkcert` for a trusted cert, for production get cert from trusted CA, do not disable verification permanently.

### Keep-Alive failure
**Meaning:** HTTP keep-alive connections failed or reset.
**Fix:** Check server/client timeout settings, verify proxy sends `Connection: keep-alive`, increase keep-alive timeout for high latency, ensure client reuses connections.

---

## 3. Server and OS-Level Errors

### `EADDRINUSE` / "Address already in use"
**Meaning:** Tried to bind a TCP port already occupied.
**Fix:** Identify process (`lsof -i :3000` or `ss -tlnp`), kill it or change port (`PORT=3001`), start in reload mode instead of second copy.

### `EACCES` / "Permission denied" when binding a port
**Meaning:** Tried to bind privileged port (below 1024) without root.
**Fix:** Prefer unprivileged ports (8000, 3000, 8080), use reverse proxy for ports 80/443, or configure user with `setcap`.

### `ECONNREFUSED` / "Connection refused"
**Meaning:** Client connected to port with no listener.
**Fix:** Verify service is running (`systemctl status`), confirm host/port in connection string, for Docker use container name as host, check firewall rules.

### `ECONNRESET` / "Connection reset by peer"
**Meaning:** Remote closed TCP connection unexpectedly.
**Fix:** Check receiving service logs, verify service healthy (not crash loop), check timeout/memory limits, verify TLS certificate validity.

### `ETIMEDOUT`
**Meaning:** Network connection or operation timed out.
**Fix:** Test connectivity (`nc -zv <host> <port>`), check DNS (`getent hosts` or `nslookup`), review timeout settings, retry after delay.

### `ENOENT` / "No such file or directory"
**Meaning:** Path does not exist or was deleted.
**Fix:** Verify path correct (typos, relative-vs-absolute), confirm file exists and process has read access, for KB docs confirm path inside `knowledge_base/` and index rebuilt.

### `ENOTDIR` / "Not a directory"
**Meaning:** Path expected to be a directory is actually a file (or vice versa).
**Fix:** Check path (`ls -la`), fix in config, recreate directory if accidentally removed.

### `EISDIR` / "Is a directory"
**Meaning:** Tried to open a directory as a regular file.
**Fix:** Verify path type, fix code to handle files/directories differently, check for loops traversing directories when a file expected.

### `EMFILE` / "Too many open files"
**Meaning:** Reached OS limit on open file descriptors.
**Fix:** Check limit (`ulimit -n`), raise if needed (`ulimit -n 65536`), find leaked handles (`lsof -p <pid>`), close sessions in `finally`/context managers.

### `ENOSPC` / "No space left on device"
**Meaning:** Disk partition full.
**Fix:** Check usage (`df -h`), find large files (`du -sh *` or `find . -type f -size +100M`), rotate logs/clean uploads, set up alerts, never delete DB files manually.

### `EPERM` / "Operation not permitted"
**Meaning:** Operation not allowed by OS or file permissions.
**Fix:** Check permissions/ownership, run with correct user, on external drives (exFAT/NTFS) be aware of filesystem limitations.

### Process crashed / exit code 1
**Meaning:** Application terminated unexpectedly.
**Fix:** Read crash logs, verify env vars, test dependency connections, check memory limits (`free -h` or Task Manager).

### Segmentation fault / SIGSEGV
**Meaning:** Process accessed memory it was not allowed to access (native modules, C extensions).
**Fix:** Reinstall affected package (`npm rebuild <package>`), check Node version compatibility, update dependency, run with `--trace-uncaught`.

### Out of memory (OOM)
**Meaning:** Exceeded available RAM.
**Fix:** Reduce workload or increase memory limits, profile memory (`node --inspect`, `memory-profiler`), fix leaks (unbounded caches, accumulated listeners), restart as temporary mitigation.

### SIGTERM (process terminated by signal)
**Meaning:** Received termination request (load balancer, container orchestrator, `kill`).
**Fix:** Handle `SIGTERM` gracefully (stop accepting new requests, drain in-flight work, close connections, exit), set shutdown timeout, verify DB/queue connections closed before exit.

---

## 4. Database and Storage Errors

### PostgreSQL: "database does not exist"
**Fix:** List DBs (`psql -l`), create if missing (`createdb`), verify connection string database name.

### PostgreSQL: "password authentication failed for user"
**Fix:** Verify password, recreate user with correct password (`CREATE USER app_user WITH PASSWORD ...`), grant privileges (`GRANT ALL PRIVILEGES ON DATABASE appdb TO app_user;`), URL-encode special chars.

### PostgreSQL: "role does not exist"
**Fix:** List roles, create role (`createuser --pwprompt app_user`), grant to database.

### PostgreSQL: "permission denied for schema public"
**Fix:** Grant usage (`GRANT USAGE ON SCHEMA public TO app_user;`), create if needed, grant table-level privs.

### PostgreSQL: "relation does not exist"
**Fix:** List tables (`\dt`), run pending migrations (`alembic upgrade head`), check table name spelling/case.

### PostgreSQL: "column does not exist"
**Fix:** Inspect schema (`\d <table_name>`), check migration, verify column spelling/case.

### PostgreSQL: "duplicate key value violates unique constraint"
**Fix:** Check unique constraint, query for duplicates, use `INSERT ... ON CONFLICT` (upsert), make jobs idempotent.

### PostgreSQL: "deadlock detected"
**Fix:** Read deadlock report, keep transactions short, acquire locks in same order, retry with backoff, add indexes.

### PostgreSQL: "too many connections"
**Fix:** Check connection count (`SELECT count(*) FROM pg_stat_activity;`), verify sessions closed, increase DB limit, implement connection pooling.

### PostgreSQL: SSL/TLS errors
**Fix:** Verify certificate, check `sslmode` (require, verify-full), for local dev use `sslmode=disable` with approval, ensure full chain.

### MySQL: "Access denied for user"
**Fix:** Verify credentials, create user (`CREATE USER 'app_user'@'%' IDENTIFIED BY 'password'`), grant (`GRANT ALL ON appdb.* TO 'app_user'@'%';`), flush privileges.

### MySQL: "Table doesn't exist" / "Unknown database"
**Fix:** List tables/databases, run migrations, verify connection string.

### Redis: "ERR connection refused"
**Fix:** Verify Redis running (`redis-cli ping` → PONG), check host/port, for Docker use container name.

### Redis: "OOM command not allowed when used memory > maxmemory"
**Fix:** Check `maxmemory` (`CONFIG GET maxmemory`), set eviction policy (`CONFIG SET maxmemory-policy allkeys-lru`), monitor memory, clean stale keys.

### S3: "NoSuchBucket"
**Fix:** Verify bucket name/region, create bucket if missing, check app configuration.

### S3: "NoSuchKey"
**Fix:** Verify object key, list objects, check case sensitivity, verify upload key.

### S3: "AccessDenied"
**Fix:** Check bucket policy, IAM policy for `s3:GetObject`/`s3:PutObject`, check bucket ACL, check CORS if browser access.

### Storage: "Access Denied" / "NoSuchKey" / "NotFound"
**Fix:** Verify bucket/object, check IAM, verify region/account, ensure correct credentials.

### Connection pool exhausted
**Fix:** Check open connections (`SELECT count(*) FROM pg_stat_activity;`), ensure sessions closed (context managers, `yield` dependencies), increase pool size if workload genuinely high, fix leaks.

### Connection string verification
**Fix:** Break string into components, URL-encode special chars, test with client tool, verify protocol (`postgresql://`, `mysql://`, `redis://`).

---

## 5. Queue, Worker, and Background-Task Errors

### RabbitMQ: "PRECONDITION_FAILED"
**Fix:** Check queue/exchange exists, verify parameters (durable, auto_delete, arguments) match across producers/consumers, delete mismatched entity in management UI.

### RabbitMQ: "CONNECTION_FORCED"
**Fix:** Check management UI for connection policy reason, verify heartbeat, increase queue limits, check TLS certs if AMQPS.

### RabbitMQ: "NOT_FOUND" (queue not found)
**Fix:** Verify queue exists, check virtual host, ensure producer declared queue before publishing.

### Kafka: "UNKNOWN_TOPIC_OR_PARTITION"
**Fix:** Create topic (`kafka-topics --create --topic <name> --partitions 3 --replication-factor 1 --bootstrap-server <host>:9092`), verify topic exists, check bootstrap server/credentials.

### Kafka: "OFFSET_OUT_OF_RANGE"
**Fix:** Check offset checkpoint, set `auto.offset.reset=earliest`, request earliest offset, verify log retention.

### Kafka: "CONSUMER_TIMEOUT_REACHED"
**Fix:** Check consumer group status, verify messages produced (`kafka-console-consumer --from-beginning`), check broker load, increase poll timeout.

### SQS: "MessageNotInflight"
**Fix:** Increase visibility timeout, make workers idempotent, check consumer logs, verify redrive policy for poison messages.

### SQS: "OverLimit" / "Queue deleted"
**Fix:** Create queue if missing, verify queue URL (region/account), check lifecycle policy.

### Celery/RQ: "TimeoutError"
**Fix:** Increase task timeout if workload genuinely long, check blocking calls in async tasks, profile task, split into subtasks, monitor worker resources.

### Celery/RQ: "WorkerLostError"
**Fix:** Check worker logs for crash traceback, verify not OOM, check for segfault, enable auto-restart (systemd/pm2), use dead-letter queues for failed messages.

### Retry / "Retrying in X seconds"
**Fix:** Check task retry settings, verify delay appropriate, ensure exception truly transient, set max retry count, log retry count.

### General queue errors
**Consumer lag:** Monitor queue depth, check worker errors, scale consumers, alert on lag thresholds.

**Poison message repeatedly fails:** Limit retries, record failure reason, route to dead-letter queue, track DLQ counters.

---

## 6. AI/LLM, Vector Store, and Provider Errors

### LLM: "rate_limit" / "Too many requests"
**Fix:** Check `Retry-After` header, use exponential backoff with jitter, check provider dashboard for quota, spread requests, debounce rapid frontend input.

### LLM: "timeout" / "Request timed out"
**Fix:** Review `LLM_TIMEOUT_SECONDS` (default 30s), check provider status, check latency distribution, for long prompts use higher timeout or smaller model, return friendly retry message.

### LLM: "invalid_api_key" / "Incorrect API key"
**Fix:** Verify env var is set and non-empty, check key format, test with SDK/curl, rotate key if exposed.

### LLM: "content_filter" / "Response blocked"
**Fix:** Review response body for filter rule, review prompt for restricted content, adjust input or use different model, log event (do not echo blocked content).

### LLM: "context_length" / "max context length"
**Fix:** Truncate/compress chat history, remove irrelevant older messages, reduce system prompt, set max context size.

### Jina embedding API: "401" / "Invalid API key"
**Fix:** Verify `JINA_API_KEY` is set and non-empty, test key directly, note `setdefault` won't overwrite existing env vars.

### Jina embedding API: "429" / "Rate limit exceeded"
**Fix:** Check `Retry-After`, implement backoff/retry, check Jina rate limits, consider higher-tier plan.

### Qdrant: "connection refused" / "No healthy nodes"
**Fix:** Verify Qdrant running, test `/health`, for Docker use container name as host, check Qdrant logs.

### Qdrant: "503" / "Service Unavailable"
**Fix:** Check health endpoint, check host resource usage, review Qdrant logs, retry with backoff (not permanent failure).

### General provider errors
**429 Too Many Requests:** Wait, check `Retry-After`, prevent duplicate submissions, use exponential backoff.

**502 Bad Gateway (upstream API):** Check status code/content-type before parsing, validate response against schema, log request ID, check provider status page.

**504 Gateway Timeout (upstream API):** Check backend logs, review `LLM_TIMEOUT_SECONDS`, check AI provider status, retry safely after delay, identify slow component.

---

## 7. Cloud Provider Errors (AWS / GCP / Azure)

### AWS: "InvalidParameter" / "InvalidParameterValue"
**Fix:** Read error for parameter name/constraint, verify against API docs, check for typos/missing fields, validate value format (ARN, date, region).

### AWS: "UnauthorizedOperation"
**Fix:** Read denied action/resource, check IAM policy, verify role trust policy, verify resource ARN (region, account), test with `aws iam simulate-principal-policy`.

### AWS: "AccessDenied"
**Fix:** Verify credentials (`aws sts get-caller-identity`), check IAM policy, check resource policy, verify credentials not expired/revoked, check temporary credentials.

### AWS: "NotFoundException" / "Resource not found"
**Fix:** Verify resource ID/ARN, list resource (AWS console), check region/account, verify correct environment.

### AWS: "LimitExceeded"
**Fix:** Read error for specific limit, request quota increase via AWS service quota console, reduce request rate, use auto-scaling/multiple resources.

### AWS S3: "NoSuchBucket" / "NoSuchKey" / "AccessDenied"
**Fix:** Verify bucket name/region, list objects, check case sensitivity, check bucket policy/IAM for `s3:GetObject`/`s3:PutObject`, check CORS for browser access.

### AWS Lambda: "InvalidParameterValueException"
**Fix:** Check error for invalid parameter, verify runtime version, adjust timeout/memory, verify execution role, check deployment package size (10 MB unzipped).

### AWS Lambda: "TooManyRequestsException"
**Fix:** Check concurrency limit, reduce invocation rate or add jitter, request concurrency increase, use async invocation with backoff.

### AWS DynamoDB: "ProvisionedThroughputExceededException"
**Fix:** Check CloudWatch metrics, add auto-scaling or increase capacity, use on-demand for unpredictable workloads, distribute keys (composite keys), implement backoff with jitter.

### AWS DynamoDB: "ConditionalCheckFailedException"
**Fix:** Verify item exists and attribute value correct, check condition expression, use `Expected` carefully (case-sensitive), retry with fresh read for optimistic locking.

### AWS API Gateway: "4XX" / "Unauthorized" / "Access Denied"
**Fix:** Check authorization type (Lambda authorizer, IAM, Cognito, API key), verify token/secret, check IAM policy, verify request headers (`x-api-key`), check throttling settings.

### AWS API Gateway: "429" / "Too Many Requests"
**Fix:** Check throttling settings, check account-level limits, implement exponential backoff with jitter, use API keys with higher limits, prevent duplicate submissions.

### AWS Cognito: "NotAuthorizedException"
**Fix:** Verify password/username, check user blocked, verify token not expired, use refresh token, check MFA status.

### AWS Cognito: "TooManyRequestsException"
**Fix:** Reduce request rate, implement exponential backoff, check for duplicate auth requests, request rate limit increase, use token cache.

### GCP: "StorageException" / "Not found" (Cloud Storage)
**Fix:** Verify bucket/object, list objects (`gsutil ls`), check case sensitivity, verify upload path.

### GCP: "PermissionDenied" (GCS)
**Fix:** Check IAM policy for bucket/object, verify service account has required role, check credentials scope, verify public access is not intended.

### GCP BigQuery: "QueryJobError" / "Query exceeded limit"
**Fix:** Check estimated bytes processed, use `LIMIT` or table scanner, use partition filters, request higher budget or on-demand, cache results.

### GCP Firebase: "The link is invalid or it has expired"
**Fix:** Verify link not expired (up to 30 days), check link parameters, regenerate link, check Firebase console for analytics.

### Azure Blob Storage: "The specified blob does not exist"
**Fix:** Verify container/blob names, list blobs (`az storage blob list`), check case sensitivity, verify upload path.

### Azure: "AuthenticationFailed"
**Fix:** Verify connection string/account key, check credentials not expired/regenerated, verify account name, check service principal credentials/scope.

---

## 8. Mobile and Web Client Errors

### CORS error: "Cross-Origin Request Blocked"
**Fix:** Verify frontend origin in backend `CORSMiddleware allow_origins`, use specific origins in production (no wildcard with credentials), check preflight OPTIONS status, confirm `allow_credentials` matches client policy.

### CORS error: "has been blocked by CORS policy"
**Fix:** Verify middleware registered before routes, check response headers (`Access-Control-Allow-Origin`, `Access-Control-Allow-Methods`, `Access-Control-Allow-Headers`), use exact frontend origin.

### Fetch/XHR: "Network Error"
**Fix:** Check Network tab and URL, test URL directly in browser, test from backend host (`curl`), verify backend listening (`ss -tlnp`), check server logs, verify DNS.

### Fetch/XHR: "Failed to fetch" (mixed content)
**Fix:** Ensure page and request use same scheme (https→https, http→http), use relative URLs or correct protocol.

### IndexedDB / localStorage errors
**Fix:** Check quota (`localStorage.length`), clear old entries, verify app served over HTTPS, check for `QuotaExceededError`.

### Service Worker errors
**Fix:** Verify SW script URL returns HTTP 200, check Console for worker errors, use "Update on reload" or unregister old worker, ensure page served over HTTPS (or localhost).

### Client-side form validation errors
**Fix:** Check Console for validation messages, verify HTML input attributes (required, pattern, min, max), add custom error handler, ensure backend also validates.

### TLS/SSL handshake failure (mobile)
**Fix:** Verify certificate valid/not expired, use correct hostname, ensure client supports TLS version/ciphers, for local dev use trusted cert (`mkcert`).

### `java.net.UnknownHostException` (Android/Java)
**Fix:** Verify URL correct/comprehensive, check DNS, test on same network, check device network connectivity.

### `TLSException` / "PKIX path building failed" (Android/Java)
**Fix:** Verify cert chain (full chain, not just leaf), use correct trust store, check device system date/time, for local dev use CA-trusted cert.

### "Connection reset" / "Broken pipe" (mobile)
**Fix:** Check device network, re-establish connection, verify server running, add retry with backoff.

---

## 9. Infrastructure, CI/CD, and Security Errors

### Kubernetes: "CrashLoopBackOff"
**Fix:** Check pod logs (`kubectl logs <pod> --previous`), check events (`kubectl describe pod <pod>`), verify health probes, check OOMKilled, verify env vars, check image pull errors.

### Kubernetes: "ImagePullBackOff" / "Failed to pull image"
**Fix:** Verify image name/tag (`docker pull <image>:<tag>`), check registry credentials, verify registry reachable, check image pull policy.

### Kubernetes: "OOMKilled"
**Fix:** Check container stats (`kubectl top pod <pod>`), review for memory leaks, increase limit if appropriate, profile with heap dumps, add alerts.

### Liveness probe failure
**Fix:** Test probe endpoint directly, verify path/port/scheme, check readiness probe, ensure liveness does not depend on external services, adjust timing settings.

### Readiness probe failure
**Fix:** Check readiness endpoint, verify dependency available, adjust `initialDelaySeconds` for startup, ensure probe does not block on optional dependencies.

### "PodSecurityPolicy" / "Forbidden"
**Fix:** Use PodSecurityStandards (restricted), run containers as non-root, set `readOnlyRootFilesystem: true`, set resource requests/limits, review security context.

### CI/CD: "npm ci" / "npm install" fails
**Fix:** Verify Node version matches `package.json` engines, delete `node_modules` and lockfile, re-run install, check for native module issues, install build tools.

### CI/CD: "yarn install" / "pnpm install" fails
**Fix:** Delete lockfile and node_modules, re-run install, verify package manager version, check native module issues, audit dependencies.

### CI/CD: "Deployment failed" (generic)
**Fix:** Check deployment logs, verify env vars set, check build output, confirm app reads platform `PORT`, review health check settings.

### Terraform: "Invalid configuration" / plan fails
**Fix:** Run `terraform fmt`, validate (`terraform validate`), check provider version, ensure required variables set, review state file (`terraform state list`).

### Terraform: "Resource already exists" / "Conflict"
**Fix:** Run `terraform plan` to see changes, check state, import if resource deleted manually (`terraform import`), reinitialize if state corrupt.

### Secrets: "Secret not found"
**Fix:** Verify secret name/key, check namespace/region, verify service account/IAM has `secrets/get`, check if secret deleted or rotated.

### Secrets: "Insufficient permissions"
**Fix:** Check IAM policy/RBAC, verify scope, grant minimum required permission (least privilege), check policy effect (Allow vs Deny), verify credentials not expired.

### TLS: "Certificate has expired" / "x509: certificate has expired"
**Fix:** Check expiry (`openssl x509 -in cert.pem -noout -enddate`), renew with certbot or cloud tool, serve full chain, set up automatic renewal, monitor expiry with alerts.

### TLS: "Certificate mismatch" / "Hostname mismatch"
**Fix:** Verify cert covers hostname (SAN), access endpoint with exact hostname on cert, use cert covering all required hostnames, ensure proxy forwards Host header.

### TLS: "Protocol / cipher mismatch"
**Fix:** Update client to modern TLS (1.2+), verify server ciphers, use TLS 1.2+ with strong ciphers, test with `openssl s_client`.

### Security: JWT/auth errors
**401 Unauthorized with valid token:** Check token expiry and claims, confirm client sends `Authorization: Bearer` header, verify signing key/issuer/audience/algorithm, refresh token or re-login, keep secrets in env vars.

**403 Forbidden:** Check RBAC, scopes, resource ownership, route guards, hosting/security logs. Do not disable security controls first.

---

## 10. Application Logs and Debugging

### Reading stack traces
1. Read the exception/error type and message first.
2. Follow traceback frames to the line of code that raised the error; in Python, the final line typically states the exception, while frames show the call path.
3. Look for the first relevant frame in your own code and inspect values.
4. Reproduce with a small, known input and add focused logging or a breakpoint.

### Debugging tools
- Python: `breakpoint()` or `import pdb; pdb.set_trace()`; VS Code debugger.
- Node.js: `node --inspect app.js` and inspect with Chrome DevTools or a supported IDE debugger.
- Logs: Use severity levels `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
- Use structured logging where possible. Log exceptions with tracebacks where appropriate, but never log passwords, auth tokens, API keys, or unnecessary personal data.

### Memory leaks
**Common causes:** Unbounded caches, retained references, accumulating event listeners, uncontrolled global state.
**Fix:** Profile memory over time (Python: `memory-profiler`; Node.js: heap snapshots), fix root cause, restart as temporary mitigation.

### High CPU usage
**Common causes:** Infinite loops, excessive computation, blocking operations inside async code, pathological regex.
**Fix:** Profile before optimizing (Python: `py-spy`; Node.js: `node --prof`), inspect hot functions, loop conditions, regex.

### Slow database queries
**Fix:** Use `EXPLAIN` / `EXPLAIN ANALYZE`, add indexes on filtered/joined columns, avoid N+1 queries (use eager loading), paginate large results.

### API versioning
**Fix:** Use consistent strategy (e.g., path prefix `/api/v1`), document supported versions, give clients time to migrate, use header or path versioning consistently.

---

## Safe Troubleshooting Rules

- Record the endpoint, timestamp, HTTP status code, and request ID if available.
- Check the response body and server logs before assuming the cause.
- Never share API keys, admin tokens, passwords, or unredacted secrets.
- Do not expose stack traces or internal implementation details to end users.
- Retry only temporary failures, and use backoff for repeated requests.
- Treat this document as general guidance; confirm exact behaviour against the deployed application.
