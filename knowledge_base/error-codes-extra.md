# Backend Error Codes — HTTP, gRPC, WebSocket, and AI/LLM Codes

## Purpose

This document covers HTTP status codes not already in `backend-http.md` (codes 100–399, and remaining 400s/500s), plus gRPC status codes, WebSocket close codes, and AI/LLM provider-specific errors. It complements `error-codes.md` (which covers the standard 4xx/5xx HTTP codes, server/OS, database, queue, cloud, mobile/web, infra/security, and debugging).

---

## 1. Unused HTTP Status Codes (100–399)

### 100 Continue
**Meaning:** The server has received the request headers and the client should proceed to send the body.
**Use case:** Response to `Expect: 100-continue` header from a client sending a large request body.
**Fix:** Send `HTTP/1.1 100 Continue` before forwarding the body to the application.

### 101 Switching Protocols
**Meaning:** The server agrees to switch protocols (e.g., to WebSocket or HTTP/2).
**Use case:** Response to `Upgrade: websocket` request.
**Fix:** Verify the `Upgrade` and `Connection` headers, then switch the protocol accordingly.

### 102 Processing
**Meaning:** The server has received and is processing the request, but no response is available yet.
**Use case:** WebDAV requests that may take a long time.
**Fix:** Keep the connection open and send `200 OK` when complete.

### 103 Early Hints
**Meaning:** The server can preview parts of the response before the full response.
**Use case:** Link headers for preloading resources.
**Fix:** Include `Link` headers with `<rel=preload>` info and continue processing.

### 203 Non-Authoritative Information
**Meaning:** The server is a transforming proxy that returned a modified version of the requested resource.
**Fix:** Verify the proxy configuration and caching headers.

### 204 No Content
**Meaning:** The request succeeded but there is no content to return.
**Use case:** DELETE request, successful form submission.
**Fix:** Return `204 No Content` with no body.

### 205 Reset Content
**Meaning:** The server successfully processed the request and the user agent should reset the document view.
**Fix:** Clear the form or UI state as appropriate.

### 206 Partial Content
**Meaning:** The server is delivering only part of the resource (byte range).
**Use case:** Range requests for large files or media.
**Fix:** Verify the `Range` header, return `Content-Range` header, support `Accept-Ranges: bytes`.

### 207 Multi-Status
**Meaning:** The message body contains multiple status codes (WebDAV).
**Fix:** Parse the XML response body for individual status codes.

### 208 Already Reported
**Meaning:** The members of a DAV binding have already been enumerated in a preceding response.
**Fix:** Use in multi-status responses; do not re-enumerate.

### 226 IM Used
**Meaning:** The server has fulfilled a GET request for the resource, and the response is a representation of the result of one or more instance manipulations applied to the current instance.
**Fix:** Return the modified representation with appropriate headers.

### 300 Multiple Choices
**Meaning:** The requested resource has multiple representations.
**Fix:** Return a list of alternatives with their URIs, or use `Content-Type: application/json`.

### 301 Moved Permanently
**Meaning:** The resource has been permanently moved to a new URI.
**Fix:** Update the client to use the new URI, send `Location` header, update bookmarks.

### 302 Found
**Meaning:** The resource is temporarily at a different URI.
**Fix:** Send `Location` header, don't change bookmarks (it's temporary).

### 303 See Other
**Meaning:** The response is at a different URI and the client should use GET to retrieve it.
**Fix:** Send `Location` header, instruct the client to use GET on that URI.

### 304 Not Modified
**Meaning:** The resource has not been modified since the last request (conditional GET).
**Fix:** Return only headers (no body), set `Last-Modified` and `ETag` correctly.

### 305 Use Proxy
**Meaning:** The requested resource must be accessed through a proxy.
**Fix:** The server should send a `Location` header with the proxy URL.

### 306 Unused
**Meaning:** This status code is no longer used in official HTTP specifications.
**Fix:** Do not rely on it; use `307` or `308` instead.

### 307 Temporary Redirect
**Meaning:** The resource is temporarily at a different URI; the method must not change.
**Fix:** Send `Location` header, keep the same HTTP method, don't convert POST to GET.

### 308 Permanent Redirect
**Meaning:** The resource has been permanently moved; the method must not change.
**Fix:** Send `Location` header, keep the same HTTP method, update clients to use the new URI.

### 400 Bad Request
**Meaning:** The request is malformed or invalid.
**Fix:** Validate request syntax, parameters, and JSON formatting.

### 401 Unauthorized
**Meaning:** Authentication is required and has failed or not been provided.
**Fix:** Provide `Authorization: Bearer` header, check token expiry, rotate keys if needed.

### 402 Payment Required
**Meaning:** Reserved for future use (often used for payment walls).
**Fix:** If the service is behind a payment wall, check subscription status, upgrade plan.

### 403 Forbidden
**Meaning:** The server understood the request but refuses to authorize it.
**Fix:** Check roles, permissions, scopes, and route guards. Do not disable security controls as a first fix.

### 404 Not Found
**Meaning:** The requested resource does not exist.
**Fix:** Verify the URL, route registration, and resource ID.

### 405 Method Not Allowed
**Meaning:** The HTTP method is not supported for this resource.
**Fix:** Configure allowed methods on the route (e.g., `allow_methods=["GET", "POST"]`).

### 406 Not Acceptable
**Meaning:** The server cannot produce a response matching the `Accept` headers.
**Fix:** Check the `Accept` header and supported response formats.

### 407 Proxy Authentication Required
**Meaning:** The client must authenticate itself with the proxy.
**Fix:** Provide proxy credentials, configure proxy authentication.

### 408 Request Timeout
**Meaning:** The request took too long and timed out.
**Fix:** Check network, backend logs, timeout settings, avoid rapid retries.

### 409 Conflict
**Meaning:** The request conflicts with the current resource state.
**Fix:** Check for duplicate records, use unique constraints, return clear error message.

### 410 Gone
**Meaning:** The resource has been permanently removed.
**Fix:** Update clients to use the replacement route, document deprecation.

### 411 Length Required
**Meaning:** The server refuses to accept the request without a `Content-Length` header.
**Fix:** Add `Content-Length` header, or use chunked transfer encoding.

### 412 Precondition Failed
**Meaning:** A precondition in the request headers failed (e.g., `If-Match`, `If-None-Match`).
**Fix:** Check the `If-Match` or `If-None-Match` header values, verify the resource version/ETag.

### 413 Payload Too Large
**Meaning:** The request body exceeds the server's limit.
**Fix:** Reduce body size, send only needed data, check server/proxy limits.

### 414 URI Too Long
**Meaning:** The request URI is too long.
**Fix:** Use POST instead of GET for large payloads, shorten query parameters, URL-encode and chunk.

### 415 Unsupported Media Type
**Meaning:** The `Content-Type` is not supported.
**Fix:** Send the expected `Content-Type` header (e.g., `application/json`).

### 416 Range Not Satisfiable
**Meaning:** The `Range` header is invalid or out of bounds.
**Fix:** Check the `Range` header against the resource size, handle gracefully.

### 417 Expectation Failed
**Meaning:** The `Expect` header could not be met.
**Fix:** Check the `Expect` header value, verify server handles it.

### 418 I'm a Teapot
**Meaning:** An Easter egg (RFC 2324). The server refuses to brew coffee.
**Fix:** This is not a real error; ignore it.

### 419
**Meaning:** Not a standard HTTP status; sometimes used by frameworks (e.g., Laravel CSRF).
**Fix:** Check the framework's CSRF protection documentation.

### 420 Method Failure
**Meaning:** Deprecated (Internet Explorer 10). Use 405 Method Not Allowed instead.
**Fix:** Replace with 405 in your API.

### 420
**Meaning:** Not a standard HTTP status; sometimes used by APIs (e.g., Twitter rate limiting).
**Fix:** Check the API documentation; often maps to 429 Too Many Requests.

### 421 Misdirected Request
**Meaning:** The request was directed at a server that cannot produce a response.
**Fix:** Verify the request was sent to the correct server/host.

### 422 Unprocessable Entity
**Meaning:** The request entity is well-formed but semantically incorrect (validation errors).
**Fix:** Check the validation details in the response body, correct field values, ensure types match schema.

### 423 Locked
**Meaning:** The resource is locked (WebDAV).
**Fix:** Check lock tokens, re-acquire lock if needed, or use `Lock-Token` header.

### 424 Failed Dependency
**Meaning:** The request failed because a dependent operation failed.
**Fix:** Inspect downstream service, return useful error, retry only for transient failures.

### 425 Too Early
**Meaning:** The server does not want to process the request risk of replay.
**Fix:** Retry after a short delay, or verify the request wasn't replayed.

### 426 Upgrade Required
**Meaning:** The client must upgrade to a different protocol.
**Fix:** Respond with `Upgrade` header indicating the required protocol.

### 427
**Meaning:** Not a standard HTTP status.
**Fix:** Do not rely on it; check API documentation.

### 428 Precondition Required
**Meaning:** The server requires a precondition header (e.g., `If-Match`).
**Fix:** Add the required precondition header, or use `If-Match`/`If-None-Match`.

### 429 Too Many Requests
**Meaning:** The client has exceeded the rate limit.
**Fix:** Wait before retrying, check for `Retry-After` header, use exponential backoff.

### 430
**Meaning:** Not a standard HTTP status; sometimes used by APIs (e.g., Shopify rate limiting).
**Fix:** Check the API documentation; often maps to 429 Too Many Requests.

### 431 Request Header Fields Too Large
**Meaning:** The server refuses the request because headers are too large.
**Fix:** Reduce header size, remove non-essential headers, split into multiple requests.

### 440
**Meaning:** Not a standard HTTP status; sometimes used by Microsoft (Internet Explorer).
**Fix:** Check the API documentation or framework documentation.

### 444
**Meaning:** Not a standard HTTP status; used by Nginx to close the connection without a response.
**Fix:** Remove the offending request; check proxy/load balancer configuration.

### 449
**Meaning:** Not a standard HTTP status; used by Microsoft for retry with action.
**Fix:** Check the documentation; often used for retry-after-action scenarios.

### 450
**Meaning:** The Windows parent platform blocked access.
**Fix:** This is Windows-specific; not applicable to backend services.

### 451 Unavailable For Legal Reasons
**Meaning:** The resource is unavailable due to legal restrictions.
**Fix:** Return 451 with a legal reason reference, or contact the service provider.

### 500 Internal Server Error
**Meaning:** An unexpected server-side failure occurred.
**Fix:** Check backend logs, verify env vars, reproduce with same request/body.

### 501 Not Implemented
**Meaning:** The server does not support the functionality required.
**Fix:** Check if the feature is implemented, upgrade the server, or use a supported endpoint.

### 502 Bad Gateway
**Meaning:** The proxy/gateway received an invalid response from upstream.
**Fix:** Verify upstream service is running, check proxy configuration, check backend logs.

### 503 Service Unavailable
**Meaning:** The service is temporarily unable to handle requests.
**Fix:** Check service health, deployment status, capacity, retry after delay.

### 504 Gateway Timeout
**Meaning:** The proxy/gateway did not receive a response in time.
**Fix:** Review timeout settings, check upstream latency, identify slow component.

### 505 HTTP Version Not Supported
**Meaning:** The server does not support the HTTP version used in the request.
**Fix:** Upgrade the client to a supported HTTP version (e.g., HTTP/1.1 or HTTP/2).

### 506 Variant Also Negotiates
**Meaning:** The server has an internal configuration error (transparent content negotiation).
**Fix:** This is a server misconfiguration; fix the content negotiation setup.

### 507 Insufficient Storage
**Meaning:** The server cannot store the representation (WebDAV).
**Fix:** Check disk space, free up storage, increase storage quota.

### 508 Loop Detected
**Meaning:** The server detected an infinite loop.
**Fix:** Check for nested or circular references, increase loop detection limits.

### 509 Bandwidth Limit Exceeded
**Meaning:** The server has exceeded its bandwidth limit.
**Fix:** Check bandwidth usage, upgrade the plan, implement bandwidth capping.

### 510 Not Extended
**Meaning:** The resource requires further extensions.
**Fix:** Implement the required extensions, or use a different endpoint.

### 511 Network Authentication Required
**Meaning:** The client must authenticate to access the network.
**Fix:** Provide network credentials, or configure a proxy for authentication.

---

## 2. gRPC Status Codes

gRPC uses its own status codes for RPC failures. They are returned in the status details, not in the gRPC status code directly.

| gRPC Code | Name | Meaning | How to troubleshoot |
|---|---|---|---|
| `0` | OK | The operation was successful. | Success; no error. |
| `1` | CANCELLED | The operation was cancelled. | Check for cancellation on the client side. |
| `2` | UNKNOWN | Unknown error. | Check logs, possibly a transient error. |
| `3` | INVALID_ARGUMENT | Client specified an invalid argument. | Check request fields, types, and values. |
| `4` | DEADLINE_EXCEEDED | The deadline expired before the operation completed. | Increase timeout, check system load, review slow dependencies. |
| `5` | NOT_FOUND | A specified resource was not found. | Verify the resource ID, check if it was deleted. |
| `6` | ALREADY_EXISTS | A resource already exists. | Check for duplicates, use upsert or check existence first. |
| `7` | PERMISSION_DENIED | The caller does not have permission. | Verify auth credentials, check IAM/RBAC policies. |
| `8` | RESOURCE_EXHAUSTED | Some resource has been exhausted. | Check rate limits, quotas, connection limits, increase pool size. |
| `9` | FAILED_PRECONDITION | The operation was rejected due to the state of the system. | Check preconditions, resource state, maintenance mode. |
| `10` | ABORTED | The operation was aborted (e.g., concurrency conflict). | Use optimistic locking, retry with backoff, check transaction conflicts. |
| `11` | OUT_OF_RANGE | Operation was attempted past the valid range. | Check indices, array bounds, date ranges, buffer sizes. |
| `12` | UNIMPLEMENTED | The operation is not implemented or enabled. | Check if the method is registered, enable the feature, check version. |
| `13` | INTERNAL | Internal server error. | Check logs, check dependency health, check config. |
| `14` | UNAVAILABLE | The service is currently unavailable. | Check service health, check dependencies, check scalability. |
| `15` | DATA_LOSS | Data loss or corruption occurred. | Check backups, restore from backup, verify data integrity. |
| `16` | UNAUTHENTICATED | The request does not have valid authentication credentials. | Provide valid auth tokens, check expiry, verify credentials. |

---

## 3. WebSocket Close Codes

WebSocket close codes are returned in the close frame to indicate why the connection was closed.

| Code | Name | Meaning | How to troubleshoot |
|---|---|---|---|
| `1000` | Normal Closure | The connection completed normally. | Expected end of conversation. |
| `1001` | Going Away | The peer is going away (e.g., server shutting down). | Check server health, handle reconnection. |
| `1002` | Protocol Error | A protocol error occurred. | Check WebSocket protocol compliance, handle fragmentation. |
| `1003` | Unsupported Data | Unsupported data type received. | Check the data format, handle unexpected message types. |
| `1004` | Reserved | Reserved for future use. | Do not encounter in production; handle gracefully. |
| `1005` | No Status Received | No close status received. | Expected in some cases; avoid logging as error. |
| `1006` | Abnormal Closure | Connection closed without a close frame. | Check network, proxy, or server crash. |
| `1007` | Invalid Frame Payload Data | Invalid payload data (e.g., non-UTF8 in text frame). | Validate the received data format, reject malformed frames. |
| `1008` | Policy Violation | Policy violation (too big, too many messages). | Implement message size limits, rate limits. |
| `1009` | Message Too Big | The message is too big to process. | Increase limits or reject large messages with `1009`. |
| `1010` | Mandatory Extension Missing | Mandatory extension not negotiated. | Check extension negotiation, or disable the extension. |
| `1011` | Internal Error | An unexpected server error occurred. | Check server logs, fix the error, prevent recurrence. |
| `1012` | Service Restart | Service is restarting. | Expected during restart; handle reconnection. |
| `1013` | Try Again Later | Temporary overload; retry later. | Use exponential backoff and retry. |
| `1014` | Bad Gateway | Server received invalid response from upstream. | Check upstream service, verify proxy configuration. |
| `1015` | TLS Handshake Failed | TLS handshake failed at the WebSocket level. | Check TLS certificate, proxy TLS configuration. |

---

## 4. AI/LLM Provider-Specific Errors

### LLM: "rate_limit" / "Too many requests"
**Meaning:** The LLM provider rejected the request because you exceeded the per-minute or per-day token/rate quota.
**Fix:** Check the `Retry-After` header, use exponential backoff with jitter, spread requests, review the provider dashboard for quota usage.

### LLM: "timeout" / "Request timed out"
**Meaning:** The LLM provider did not respond within the configured timeout.
**Fix:** Review `LLM_TIMEOUT_SECONDS` (default 30s), check provider status, review latency distribution, for long prompts use a higher timeout or smaller model.

### LLM: "invalid_api_key" / "Incorrect API key"
**Meaning:** The API key is missing, malformed, or wrong.
**Fix:** Verify the environment variable is set and non-empty, check the key format, test with the provider's CLI, rotate the key if exposed.

### LLM: "content_filter" / "Response blocked"
**Meaning:** The provider's safety filter blocked the request or response.
**Fix:** Review the response body for the filter rule, review the prompt for restricted content, adjust the input or use a different model, log the event.

### LLM: "context_length" / "max context length"
**Meaning:** The prompt exceeds the model's maximum context window.
**Fix:** Truncate or compress chat history, remove older messages, reduce the system prompt, set a max context size.

### LLM: "model_not_found" / "Model does not exist"
**Meaning:** The requested model ID is invalid or unavailable.
**Fix:** Check the model ID spelling, list available models on the provider dashboard, verify the model is enabled, fall back to a known model.

### LLM: "service_unavailable" / "Provider temporarily unavailable"
**Meaning:** The LLM provider is down or overloaded.
**Fix:** Check the provider's status page, retry with backoff, use a fallback model or generic LLM, check provider incident feeds.

### LLM: "insufficient_quota" / "Quota exceeded"
**Meaning:** Your account has exceeded its monthly or daily quota.
**Fix:** Review usage on the provider dashboard, upgrade the plan, reduce request volume, set up alerts on quota usage.

### LLM: "token_limit_exceeded" / "Too many tokens"
**Meaning:** The request exceeded the token limit for a single call.
**Fix:** Truncate the prompt, reduce chat history, split the request into smaller chunks, use a longer-context model.

### LLM: "streaming_error" / "Stream interrupted"
**Meaning:** The streaming response was cut off.
**Fix:** Check network stability, retry the request with streaming enabled, handle partial results gracefully.

### LLM: "embedding_error" / "Embedding generation failed"
**Meaning:** Failed to generate embeddings for a document.
**Fix:** Check the embedding model configuration, verify the API key, check the document size, retry with a smaller chunk.

### LLM: "knowledge_base_disabled"
**Meaning:** The knowledge base is not configured or index is missing.
**Fix:** Check `GET /kb/status`, verify `KB_ENABLED`, `JINA_API_KEY`, Qdrant configuration, rebuild the index after adding documents.

### LLM: "knowledge_base_index_missing"
**Meaning:** The vector index has not been built.
**Fix:** Call `POST /kb/rebuild`, check Qdrant connection, verify `JINA_API_KEY`, check server logs.

### LLM: "widget_not_found" / "Script URL wrong"
**Meaning:** The embedded widget script could not be loaded.
**Fix:** Verify the script URL points to `/widget.js` on the correct backend host, check `data-api-url` attribute, inspect Console and Network errors.

---

## 5. Kubernetes-Specific Errors

### `CrashLoopBackOff`
**Meaning:** The pod keeps crashing and Kubernetes is repeatedly restarting it with back-off delays.
**Fix:** Check pod logs (`kubectl logs <pod> --previous`), check events (`kubectl describe pod <pod>`), verify health probes, check env vars, verify image pull.

### `ImagePullBackOff` / "Failed to pull image"
**Meaning:** Kubernetes could not pull the container image.
**Fix:** Verify the image name and tag, check registry credentials, verify the registry is reachable, check the image pull policy, test `docker pull <image>`.

### `OOMKilled` / "Out of memory"
**Meaning:** The container was killed because it exceeded its memory limit.
**Fix:** Check container stats (`kubectl top pod <pod>`), review the app for memory leaks, increase the memory limit if appropriate, profile with heap dumps.

### Liveness probe failure
**Meaning:** Kubernetes considers the container unhealthy and restarts it.
**Fix:** Test the probe endpoint directly, verify path/port/scheme, check if it depends on external services, adjust timing settings (`initialDelaySeconds`, `periodSeconds`).

### Readiness probe failure
**Meaning:** Kubernetes marks the pod as not ready and stops sending traffic.
**Fix:** Check the readiness endpoint, verify the dependency is available, adjust `initialDelaySeconds` for startup time, verify the probe doesn't depend on optional services.

### `PodSecurityPolicy` / "Forbidden"
**Meaning:** The pod's security context or resource requests violate policy.
**Fix:** Use a PodSecurityPolicy or PodSecurityStandards (restricted mode), run containers as non-root, set `readOnlyRootFilesystem: true`, set resource requests/limits.

### `ImagePullErr` / "Cluster DNS not found"
**Meaning:** The pod cannot resolve service names via DNS.
**Fix:** Verify the service is created, check the cluster DNS add-on, verify the service name and namespace, check the pod's DNS configuration.

### `BackOff` (generic)
**Meaning:** Kubernetes is backing off on restarts (generic error).
**Fix:** Identify the specific error from pod logs, check the previous log (`kubectl logs --previous`), fix the root cause.

---

## 6. Monitoring and Observability Errors

### Prometheus scraping errors
**Meaning:** Prometheus cannot scrape metrics from the application.
**Fix:** Verify the `/metrics` endpoint returns HTTP 200, check the scrape configuration, verify the metrics endpoint path, check TLS certificates if using HTTPS.

### Grafana dashboard errors
**Meaning:** Dashboards fail to load or display data.
**Fix:** Check the Prometheus datasource connection in Grafana, verify the metrics endpoint, check for missing data or time ranges, verify the dashboard query.

### OpenTelemetry errors
**Meaning:** Distributed tracing fails or samples are dropped.
**Fix:** Verify the OTel collector is reachable, check the exporter configuration, verify the trace context propagation, check for missing spans or attributes.

### Health check endpoint returns 503
**Meaning:** The `/health` endpoint reports the service is unhealthy.
**Fix:** Check the health endpoint code, verify required dependencies (DB, cache, queue) are available, separate liveness from readiness, check the reported status fields.

### Metrics endpoint returns 404
**Meaning:** `/metrics` endpoint not found.
**Fix:** Verify the metrics library is initialized, check the route path, ensure the metrics server is running, test with `curl /metrics`.

---

## 7. Chatbot Application-Specific Errors

### Widget: script URL wrong
**Meaning:** The embedded chat widget cannot load the script.
**Fix:** Verify the script URL points to `/widget.js` on the correct backend host, check `data-api-url` attribute contains the backend base URL without a trailing slash, inspect Console and Network errors, check hosting logs.

### Widget: `data-api-url` has trailing slash
**Meaning:** The script URL attribute has a trailing slash, causing the widget to fail.
**Fix:** Remove the trailing slash from `data-api-url`, ensure it contains the backend base URL without trailing slash.

### Dashboard: KB not enabled
**Meaning:** The dashboard shows the knowledge base is disabled.
**Fix:** Check `GET /kb/status`, verify `KB_ENABLED`, `JINA_API_KEY`, Qdrant configuration, rebuild the index after adding documents.

### Chat: chatbot gives no knowledge-based answer
**Fix:** Call `GET /kb/status`, confirm `enabled` is `true`, verify embedding/vector-store config, confirm source documents are in `knowledge_base/`, rebuild the index after adding or changing documents.

### Chat: `POST /kb/rebuild` fails
**Fix:** Confirm backend is running and URL is correct, if `KB_ADMIN_TOKEN` is set send the matching `x-kb-admin-token` header, check Jina embedding and Qdrant configuration, review server logs.

### Chat: `GET /kb/status` reports KB disabled
**Meaning:** The KB may not be ready for retrieval.
**Fix:** Check `KB_ENABLED`, `JINA_API_KEY`, Qdrant/vector-store config, whether the index was built successfully, verify config before treating as an app bug.

### Chat: widget does not load
**Fix:** Open `/health`, confirm the script URL points to `/widget.js`, check `data-api-url` attribute, inspect Console and Network errors, check hosting logs.

### Chat: LLM returns 503
**Meaning:** The LLM provider is temporarily unavailable.
**Fix:** Check `GET /health` and its reported status, verify LLM configuration, review application logs and provider status, retry after short delay with backoff.

### Chat: LLM returns 504
**Meaning:** The LLM provider did not respond in time.
**Fix:** Check backend logs and upstream request timing, review `LLM_TIMEOUT_SECONDS` and hosting/proxy timeout settings, check AI provider status, retry safely after delay.

### Chat: LLM returns 429
**Meaning:** Rate limited by the AI provider.
**Fix:** Wait before retrying, check for `Retry-After` header, prevent duplicate submissions in the frontend, review backend and AI-provider rate limits, use exponential backoff.

---

## 8. App-Specific Errors (Frontend/Dashboard)

### Frontend: mixed content
**Meaning:** A secure page loads an insecure resource.
**Fix:** Ensure page and resource use the same scheme, use relative URLs or correct protocol, serve everything over HTTPS in production.

### Frontend: CORS error — "Cross-Origin Request Blocked"
**Fix:** Verify the frontend origin is in the backend's `CORSMiddleware allow_origins`, use a specific origin list in production, check the preflight response, confirm `allow_credentials` matches the frontend's credential policy.

### Frontend: Service Worker errors
**Fix:** Verify the SW script URL returns HTTP 200, check the Console for errors, unregister old workers, ensure the page is served over HTTPS (or localhost).

### Dashboard: session expired
**Fix:** Check server-side session settings and cookie `Max-Age`/`Expires`, ensure the client sends the cookie, extend the lifetime if appropriate, or prompt re-login.

### Dashboard: CSRF token validation failed
**Fix:** Include the token as required by the framework, verify cookie and origin settings, do not disable CSRF protection as a general workaround.

### API: unhandled promise rejection
**Fix:** Always catch async errors, use `try/catch` in async handlers, use a wrapper for Express, don't rely on unhandled rejections.

### API: Nodemon not restarting
**Fix:** Check `nodemon.json` ignore patterns, ensure the changed file is within watched paths, check filesystem watcher limits (`fs.inotify.max_user_watches`), restart manually with `rs`.

### API: EPERM on npm (external drives)
**Fix:** exFAT/NTFS drives lack symlink support, move the project to the internal ext4 filesystem and run npm there.

---

## Diagnostic Checklist

1. **Identify the layer** — HTTP, gRPC, WebSocket, LLM, K8s, observability, or app-specific.
2. **Record the error code and full message** — don't truncate.
3. **Identify the category** — network, database, auth, config, timeout, or resource limit.
4. **Check the health endpoint** — `GET /health` and its reported status.
5. **Check logs** — backend, deployment, provider, and hosting logs.
6. **Verify configuration** — env vars, secrets, TLS, health probe settings.
7. **Check dependencies** — DB, cache, queue, vector store, LLM provider.
8. **Reproduce** — send a single test request in a clean environment.
9. **Implement a fallback** — don't let a provider failure take down the whole app.
10. **Document** — symptom, root cause, fix, and prevention steps.
