# Backend Troubleshooting — HTTP Errors and API Reference

## Purpose

This document is a troubleshooting reference for common backend/API errors in the `website-ai-chatbot` project. It is intended for the chatbot knowledge base.

The project uses a FastAPI backend and exposes these relevant endpoints:

- `GET /health` — checks backend liveness and reports LLM/knowledge-base status.
- `GET /kb/status` — reports whether the knowledge base is configured and indexed.
- `POST /kb/rebuild` — rebuilds the knowledge-base vector index.
- `POST /api/chat` — accepts a chat message and returns an assistant reply.
- `GET /widget.js` — serves the embeddable chat widget.

**Important:** HTTP status codes below describe common meanings. The exact response for a particular failure depends on the backend implementation, hosting platform, and upstream provider. Check the response body and server logs before deciding on a fix. This project documents error responses in the shape `{"error": "human-readable message"}`.

---

## HTTP Status Code Reference

### 400 — Bad Request

**Meaning:** The server cannot process the request because the request data is invalid or malformed.

**Common causes**
- The JSON body is malformed.
- A required field such as `message` is missing.
- A field has the wrong data type.
- The client sends an unsupported request format.

**How to troubleshoot**
1. Check that the request body is valid JSON.
2. For `POST /api/chat`, confirm that `message` is a string.
3. Confirm that `history`, if supplied, follows the expected format of role/content objects.
4. Read the error message returned by the API and correct the request.

**Example**
```json
{
  "message": "Hello",
  "history": []
}
```

### 401 — Unauthorized

**Meaning:** The request requires valid authentication, but the credentials are missing or invalid.

**Common causes**
- A protected endpoint requires a token.
- The admin token is missing or incorrect.
- An environment variable used for authentication is not configured as expected.

**How to troubleshoot**
1. Check whether the endpoint requires authentication.
2. For `POST /kb/rebuild`, check whether `KB_ADMIN_TOKEN` is configured.
3. If the token is configured, send the matching `x-kb-admin-token` header.
4. Do not put secret tokens in public frontend code or commit them to Git.

**Note:** The documented rebuild endpoint requires the header when `KB_ADMIN_TOKEN` is set. Do not assume every endpoint requires authentication.

### 403 — Forbidden

**Meaning:** The server understood the request but refuses to allow it.

**Common causes**
- The credentials are valid but do not have permission.
- A hosting or security rule blocks the request.
- The request is blocked by a proxy or platform policy.

**How to troubleshoot**
1. Confirm that the endpoint is intended to be publicly accessible.
2. Check authentication and authorization settings.
3. Review hosting, reverse-proxy, and security logs.
4. Do not disable security controls as a first fix.

### 404 — Not Found

**Meaning:** The requested route or resource does not exist at the URL being called.

**Common causes**
- The API URL or route path is misspelled.
- The frontend is configured with the wrong backend base URL.
- The deployment is serving an older version of the application.
- The request is sent to the wrong host or path.

**How to troubleshoot**
1. Verify the backend base URL and route path.
2. Check the documented routes: `/health`, `/widget.js`, `/kb/status`, `/kb/rebuild`, and `/api/chat`.
3. Open `GET /health` to confirm that the expected backend is reachable.
4. Check deployment logs if a route expected to exist returns 404.

### 405 — Method Not Allowed

**Meaning:** The URL exists, but the endpoint does not support the HTTP method used.

**Fix:** Check whether the client should use GET, POST, PUT, PATCH, or DELETE. Configure allowed methods on the route and return an appropriate Allow header.

### 406 — Not Acceptable

**Meaning:** The server cannot return a response in any format listed in the request's Accept header.

**Fix:** Check the client's Accept header and the response formats supported by the API. Document supported content types.

### 408 — Request Timeout

**Meaning:** The request took too long and timed out.

**Common causes**
- Network connectivity is slow or unstable.
- The backend is busy.
- An upstream AI provider takes too long to respond.

**How to troubleshoot**
1. Retry once after checking network connectivity.
2. Check backend logs and upstream-provider status.
3. Review timeout settings, including `LLM_TIMEOUT_SECONDS` (documented default: `30` seconds).
4. Avoid repeated rapid retries that can increase load.

### 409 — Conflict

**Meaning:** The request conflicts with the current state of a resource, such as creating a record that already exists.

**Fix:** Check for duplicate records and state changes. Use unique constraints and return a clear conflict message. For concurrent updates, consider version fields or optimistic locking.

### 410 — Gone

**Meaning:** The resource was intentionally removed and is no longer available.

**Fix:** Confirm whether the endpoint or resource is retired. Update clients to use the replacement route and document the deprecation.

### 413 — Payload Too Large

**Meaning:** The request body exceeds the maximum size accepted by the server or an intermediary.

**Common causes**
- The client sends an unusually large request.
- Chat history is too long.
- A proxy or hosting platform has a smaller body-size limit.

**How to troubleshoot**
1. Reduce the request body size.
2. Send only the conversation history needed for the current question.
3. Check server and proxy body-size limits.
4. If this project's documented 10 MB request-body guard is active, ensure the request is below that limit.

### 415 — Unsupported Media Type

**Meaning:** The request's Content-Type is not supported by the endpoint.

**Fix:** Send the expected content type, such as application/json, and verify that the server has the required parser or upload handler enabled.

### 416 — Range Not Satisfiable

**Meaning:** A requested byte range falls outside the available content.

**Fix:** Check the Range header and the current file size. If range requests are unsupported, handle them consistently and document the behavior.

### 424 — Failed Dependency

**Meaning:** The request failed because an operation it depends on failed.

**Fix:** Inspect the downstream service or prerequisite operation. Return a useful error without exposing internal details, and consider retries only for transient failures.

### 429 — Too Many Requests

**Meaning:** The client has sent too many requests within a limited period.

**Common causes**
- The client sends requests repeatedly or in a tight loop.
- Multiple users share a rate limit.
- A hosting platform or upstream AI provider applies rate limiting.

**How to troubleshoot**
1. Wait before retrying.
2. Check whether the response includes a `Retry-After` header.
3. Prevent accidental duplicate submissions in the frontend.
4. Review backend and AI-provider rate limits.
5. Use exponential backoff for automated retries.

### 500 — Internal Server Error

**Meaning:** The backend encountered an unexpected condition and could not complete the request.

**Common causes**
- An unhandled exception in application code.
- Invalid or missing runtime configuration.
- A failure while processing a request or knowledge-base document.
- An unexpected error from a dependency.

**How to troubleshoot**
1. Check backend logs at the exact time of the request.
2. Confirm required environment variables are configured.
3. Reproduce the issue with the same endpoint and request body.
4. Check recent code or deployment changes.
5. Return a safe error message to the client; never expose API keys, stack traces, or internal secrets.

### 502 — Bad Gateway

**Meaning:** A gateway or proxy received an invalid response from the backend or an upstream service.

**Common causes**
- The application process is down or restarting.
- A reverse proxy points to the wrong host or port.
- An upstream service closes the connection unexpectedly.
- The backend crashes while processing the request.

**How to troubleshoot**
1. Check whether the application is running.
2. Test `GET /health`.
3. Review application and reverse-proxy logs.
4. Verify the configured upstream address and port.
5. Check whether the issue is caused by the backend host or an external provider.

### 503 — Service Unavailable

**Meaning:** The service is temporarily unable to handle the request.

**Common causes**
- The backend is restarting, overloaded, or temporarily unavailable.
- The hosting platform has suspended or restarted the service.
- A required upstream service is unavailable.
- The service is not ready after deployment.

**How to troubleshoot**
1. Check service availability and deployment status.
2. Call `GET /health` and inspect its reported status.
3. Check whether required LLM or knowledge-base configuration is available.
4. Review application logs and provider status.
5. Retry after a short delay; use backoff rather than continuous retries.

**Important distinction:** A knowledge base that is not configured may cause the chatbot to operate in its documented fallback mode. Check `/kb/status` rather than assuming every knowledge-base issue is a 503.

### 504 — Gateway Timeout

**Meaning:** A gateway or proxy did not receive a response from the backend or upstream service in time.

**Common causes**
- An AI-provider response is slow.
- The backend is waiting on a network or external-service call.
- The proxy timeout is shorter than the operation's completion time.

**How to troubleshoot**
1. Check backend logs and the timing of the upstream request.
2. Review `LLM_TIMEOUT_SECONDS` and hosting/proxy timeout settings.
3. Check the status of the configured AI provider.
4. Retry safely after a delay.
5. Do not increase timeouts blindly; first identify which component is slow.

---

## Data Validation and Serialization

### File Upload Format Error

**Cause:** The upload uses an unsupported format or the multipart form is incorrectly constructed.

**Fix:** Use the expected multipart field name and let the HTTP client set the multipart boundary. Validate file type and size on the server rather than trusting the filename alone.

### Serialization Error

**Cause:** The response encoder cannot convert a custom object, date, decimal, or database type into JSON.

**Fix:** Convert values to supported representations, such as ISO 8601 strings for dates and documented numeric or string formats for decimals. Use a consistent response schema.

### Missing Required Field

**Cause:** The client omitted a field required by the API contract.

**Fix:** Check the request schema and required fields. Return a field-level validation error and keep API documentation synchronized with the implementation.

### Invalid Pagination Parameters

**Cause:** Page number, page size, limit, or offset is negative, malformed, or unreasonably large.

**Fix:** Validate parameters at the API boundary, set a maximum page size, and return a 400 response for invalid values.

### Unicode or Character-Encoding Problems

**Cause:** Data is decoded using the wrong character encoding or the database and application use inconsistent encodings.

**Fix:** Standardize on UTF-8 where appropriate, verify database column encoding, and test with non-English text and emoji.

---

## Caching and Concurrency

### Stale Cache Response

**Cause:** Cached data was not invalidated after the underlying record changed.

**Fix:** Define cache expiration and invalidation rules. Invalidate or update relevant keys after writes, and use versioned keys when appropriate.

### Cache Stampede

**Cause:** Many requests attempt to rebuild the same expired cache entry simultaneously.

**Fix:** Use request coalescing, a short lock, stale-while-revalidate, or randomized expiration. Keep the fallback database path within capacity.

### Race Condition During Updates

**Cause:** Multiple requests read and modify the same state at the same time.

**Fix:** Use database transactions, atomic updates, unique constraints, or optimistic locking. Reproduce the issue with concurrent tests.

### Deadlock Detected

**Cause:** Two or more transactions hold locks that the others need.

**Fix:** Keep transactions short, acquire locks in a consistent order, and inspect the database deadlock report. Retry only the full transaction when the database marks the error as retryable.

### Duplicate Job Execution

**Cause:** A queue or scheduler delivers a job more than once, or a worker retries after the result was already committed.

**Fix:** Make jobs idempotent. Use a unique job key or idempotency record, and acknowledge messages only after successful processing.

---

## Queues and External Services

### Message Queue Consumer Lag

**Cause:** Messages arrive faster than workers can process them, or workers are failing repeatedly.

**Fix:** Monitor queue depth and processing time. Check worker errors, scale consumers carefully, and use bounded retries with a dead-letter queue.

### Poison Message Repeatedly Fails

**Cause:** A malformed or unsupported message fails every processing attempt.

**Fix:** Limit retries, record the failure reason safely, and route the message to a dead-letter queue for inspection. Do not let one message block the entire queue.

### External API Returns Unexpected Response

**Cause:** The provider changed its schema, returned HTML instead of JSON, or sent an undocumented status.

**Fix:** Check status code and content type before parsing. Validate responses against a schema, log a request or correlation ID, and handle unknown fields or statuses safely.

### Retry Storm

**Cause:** Many requests retry a failing dependency at the same time, increasing its load.

**Fix:** Use exponential backoff with jitter, set retry limits, and apply circuit breaking. Do not automatically retry non-idempotent operations unless they use an idempotency key.

### Webhook Signature Verification Failed

**Cause:** The signing secret is incorrect, the raw request body changed, or the signature header is parsed incorrectly.

**Fix:** Use the provider's exact signature algorithm and raw request bytes. Compare signatures with a constant-time comparison and keep webhook secrets out of logs.

---

## Security and Configuration

### CSRF Token Validation Failed

**Cause:** A state-changing request is missing a valid anti-CSRF token or the token does not match the session.

**Fix:** Include the token as required by the framework, verify cookie and origin settings, and do not disable CSRF protection as a general workaround.

### Secret or Configuration Value Missing

**Cause:** An environment variable is absent, misspelled, or unavailable in the deployment environment.

**Fix:** Validate required configuration at startup and fail with a clear, non-sensitive message. Check deployment settings without printing secret values.

### Permission Denied When Writing a File

**Cause:** The service account lacks access to the target directory, or the path is read-only.

**Fix:** Check the process user and directory permissions. Grant only the minimum required access and avoid running the whole service as an administrator.

### Request Rejected by Rate Limiter

**Cause:** The client exceeded a configured request quota.

**Fix:** Return 429 Too Many Requests with a suitable Retry-After value when possible. Review per-user or per-IP limits and use backoff on the client. Do not remove rate limiting without assessing abuse risk.

### Insecure Direct Object Reference (IDOR)

**Cause:** The backend accepts a resource ID without checking whether the authenticated user is allowed to access that resource.

**Fix:** Enforce authorization on every object read and write. Test access with a different user's ID and avoid relying on hidden UI controls as protection.

---

## Observability and Reliability

### Correlation ID Missing

**Cause:** Requests cannot be connected across application logs and downstream services.

**Fix:** Generate or validate a request ID at the entry point, pass it to downstream calls, and include it in structured logs. Do not trust arbitrary IDs as authentication.

### Health Endpoint Returns Success While Dependencies Are Down

**Cause:** The health check only verifies that the process is running.

**Fix:** Separate liveness checks from readiness checks. Readiness may verify critical dependencies with short timeouts; avoid making liveness depend on every external service.

### Graceful Shutdown Fails

**Cause:** The process exits before in-flight requests or background jobs finish.

**Fix:** Handle termination signals, stop accepting new work, drain active requests, and close database and queue connections within a defined shutdown timeout.

### Disk Space Exhausted

**Cause:** Logs, temporary files, uploads, or database files consumed available storage.

**Fix:** Check disk usage and log rotation, remove only safe temporary data, and alert before storage reaches capacity. Never delete database files manually to free space.

### Clock Skew Between Services

**Cause:** Servers have different system times, causing token, signature, or event-timestamp validation failures.

**Fix:** Synchronize hosts using a reliable time service, monitor clock drift, and allow only a small documented tolerance where the protocol requires it.

### Error Messages Expose Internal Details

**Cause:** Debug traces, SQL errors, file paths, or secrets are returned to clients.

**Fix:** Return a generic public error with a request ID. Keep detailed diagnostics in access-controlled logs and disable debug output in production.

---

## Knowledge Base Troubleshooting

### Problem: The chatbot gives no knowledge-based answer

**Check**
1. Call `GET /kb/status`.
2. Confirm that `enabled` is `true`.
3. Confirm that embedding and vector-store configuration is present.
4. Confirm that source documents are inside `knowledge_base/`.
5. Rebuild the index after adding or changing documents.

**Rebuild command**
```bash
python3 -m scripts.rebuild_index
```

**Expected result:** The command reports document, chunk, and stored counts. If rebuilding fails, inspect the full command output and backend configuration.

### Problem: `POST /kb/rebuild` fails

**Check**
- Confirm the backend is running and the URL is correct.
- If `KB_ADMIN_TOKEN` is set, send the matching `x-kb-admin-token` header.
- Check Jina embedding and Qdrant configuration.
- Review server logs for the actual error.

### Problem: `GET /kb/status` reports the knowledge base is disabled

**Meaning:** The knowledge base may not yet be ready for retrieval.

**Check**
- `KB_ENABLED` setting.
- `JINA_API_KEY`.
- Qdrant/vector-store configuration.
- Whether the index has been built successfully.

A disabled knowledge base before the first index build or while required keys are missing can be expected; verify configuration before treating it as an application bug.

### Problem: The widget does not load

**Check**
1. Open the backend's `/health` endpoint.
2. Confirm that the script URL points to `/widget.js` on the correct backend host.
3. Confirm the `data-api-url` attribute contains the backend base URL without a trailing slash.
4. Open browser Developer Tools and inspect Console and Network errors.
5. Check hosting logs if the script request returns 5xx.

---

### WebSocket Close Codes

| Code | Name | Meaning | How to troubleshoot |
|---|---|---|---|
| `1000` | Normal Closure | Connection completed normally. | Expected end of conversation. |
| `1001` | Going Away | Peer going away (server shutting down). | Check server health, handle reconnection. |
| `1002` | Protocol Error | A protocol error occurred. | Check WebSocket protocol compliance, handle fragmentation. |
| `1003` | Unsupported Data | Unsupported data type received. | Check the data format, handle unexpected message types. |
| `1005` | No Status Received | No close status received. | Expected in some cases; avoid logging as error. |
| `1006` | Abnormal Closure | Connection closed without a close frame. | Check network, proxy, or server crash. |
| `1007` | Invalid Frame Payload Data | Invalid payload data (non-UTF8 in text frame). | Validate the received data format, reject malformed frames. |
| `1008` | Policy Violation | Policy violation (too big, too many messages). | Implement message size limits, rate limits. |
| `1009` | Message Too Big | Message too big to process. | Increase limits or reject large messages with `1009`. |
| `1010` | Mandatory Extension Missing | Mandatory extension not negotiated. | Check extension negotiation, or disable the extension. |
| `1011` | Internal Error | Unexpected server error. | Check server logs, fix the error, prevent recurrence. |
| `1012` | Service Restart | Service is restarting. | Expected during restart; handle reconnection. |
| `1013` | Try Again Later | Temporary overload; retry later. | Use exponential backoff and retry. |
| `1014` | Bad Gateway | Invalid response from upstream. | Check upstream service, verify proxy configuration. |
| `1015` | TLS Handshake Failed | TLS handshake failed at WebSocket level. | Check TLS certificate, proxy TLS configuration. |

### gRPC Status Codes

gRPC uses its own status codes for RPC failures, returned in the status details:

| gRPC Code | Name | Meaning | How to troubleshoot |
|---|---|---|---|
| `0` | OK | Operation successful. | Success; no error. |
| `1` | CANCELLED | Operation cancelled. | Check client-side cancellation. |
| `2` | UNKNOWN | Unknown error. | Check logs, possibly transient. |
| `3` | INVALID_ARGUMENT | Invalid argument specified. | Check request fields, types, values. |
| `4` | DEADLINE_EXCEEDED | Deadline expired before completion. | Increase timeout, check system load, review slow dependencies. |
| `5` | NOT_FOUND | Resource not found. | Verify resource ID, check if deleted. |
| `6` | ALREADY_EXISTS | Resource already exists. | Check for duplicates, use upsert or check existence first. |
| `7` | PERMISSION_DENIED | Caller lacks permission. | Verify auth credentials, check IAM/RBAC policies. |
| `8` | RESOURCE_EXHAUSTED | Resource exhausted. | Check rate limits, quotas, connection limits, increase pool size. |
| `9` | FAILED_PRECONDITION | Operation rejected due to system state. | Check preconditions, resource state, maintenance mode. |
| `10` | ABORTED | Operation aborted (e.g., concurrency conflict). | Use optimistic locking, retry with backoff, check transaction conflicts. |
| `11` | OUT_OF_RANGE | Operation past valid range. | Check indices, array bounds, date ranges, buffer sizes. |
| `12` | UNIMPLEMENTED | Operation not implemented or enabled. | Check if method is registered, enable the feature, check version. |
| `13` | INTERNAL | Internal server error. | Check logs, dependency health, config. |
| `14` | UNAVAILABLE | Service currently unavailable. | Check service health, dependencies, scalability. |
| `15` | DATA_LOSS | Data loss or corruption. | Check backups, restore, verify data integrity. |
| `16` | UNAUTHENTICATED | Request lacks valid auth credentials. | Provide valid auth tokens, check expiry, verify credentials. |

---

### LLM: knowledge_base_widget_not_found / widget script wrong
**Meaning:** The embedded widget script could not be loaded or the API URL is wrong.
**Fix:** Verify the script URL points to `/widget.js` on the correct backend host, check `data-api-url` attribute contains the backend base URL without a trailing slash, inspect Console and Network errors, check hosting logs.

### LLM: Knowledge Base Troubleshooting Quick Reference

| KB problem | What to check | Fix |
|---|---|---|
| Chatbot gives no KB answer | `GET /kb/status` returns `enabled=false`? | Rebuild index: `python3 -m scripts.rebuild_index` |
| `POST /kb/rebuild` fails | Backend running? `x-kb-admin-token` header? | Check backend logs, verify Jina embedding + Qdrant config |
| KB reports disabled | `KB_ENABLED`, `JINA_API_KEY`, Qdrant config? | Verify configuration before treating as app bug |
| Widget does not load | Script URL, `data-api-url` without trailing slash? | Inspect Console/Network errors, check hosting logs |

---

## Safe Troubleshooting Rules

|| Error code | Name | First thing to check |
||---|---|---|
|| 400 | Bad Request | Request body and required fields |
|| 401 | Unauthorized | Token or authentication requirement |
|| 403 | Forbidden | Permissions and security rules |
|| 404 | Not Found | URL, route, and backend base URL |
|| 408 | Request Timeout | Network and request duration |
|| 413 | Payload Too Large | Request body size |
|| 429 | Too Many Requests | Rate limit and retry policy |
|| 500 | Internal Server Error | Backend logs and configuration |
|| 502 | Bad Gateway | Backend process and proxy/upstream |
|| 503 | Service Unavailable | Service health and dependencies |
|| 504 | Gateway Timeout | Upstream response time and timeout settings |

---

## Safe Troubleshooting Rules

- Record the endpoint, timestamp, HTTP status code, and request ID if available.
- Check the response body and server logs before assuming the cause.
- Never share API keys, admin tokens, passwords, or unredacted secrets.
- Do not expose stack traces or internal implementation details to end users.
- Retry only temporary failures, and use backoff for repeated requests.
- Treat this document as general guidance; confirm exact behaviour against the deployed application.
