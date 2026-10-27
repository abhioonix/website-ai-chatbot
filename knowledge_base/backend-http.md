# Backend Troubleshooting — HTTP Errors and API Reference

## Purpose

This document is a platform-agnostic troubleshooting reference for common backend/API errors across all backend types (Python/FastAPI, Node.js/Express, etc.). It is intended for use as a general knowledge base for any backend application.

HTTP status codes below describe common meanings. The exact response for a particular failure depends on the backend implementation, framework, hosting platform, and upstream provider. Check the response body and server logs before deciding on a fix.

**General error response shape:** `{\"error\": \"human-readable message\"}` (adjust to your API contract).

**General troubleshooting rule:** Always check the response body and server logs before assuming the cause. Never expose secrets, tokens, stack traces, or internal implementation details to end users.

---

## HTTP Status Code Reference

### 400 — Bad Request

**Meaning:** The server cannot process the request because the request data is invalid or malformed.

**Common causes**
- The JSON body is malformed.
- A required field is missing.
- A field has the wrong data type.
- The client sends an unsupported request format.

**How to troubleshoot**
1. Check that the request body is valid JSON.
2. Validate the request against the API schema (Pydantic, Joi, Zod, etc.).
3. Check field types, required fields, and format constraints.
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
- Admin token missing or incorrect.
- API key invalid or expired.
- Token not sent in the `Authorization: Bearer` header.

**How to troubleshoot**
1. Check which authentication mechanism is required.
2. Verify the token/API key is present and correctly formatted.
3. Check token expiry.
4. Verify credentials are not expired or revoked.
5. Never commit tokens or secrets to version control.

### 403 — Forbidden

**Meaning:** The server understood the request but refuses to allow it.

**Common causes**
- Valid credentials but insufficient permissions.
- RBAC/role-based access control rules.
- API key lacks required scope.
- Hosting/security rule or proxy/platform policy.

**How to troubleshoot**
1. Check RBAC rules and resource ownership.
2. Verify API key scope and permissions.
3. Check security logs for the denied action.
4. Do not disable security controls as a first fix.
5. Review route guards and middleware.

### 404 — Not Found

**Meaning:** The requested route or resource does not exist.

**Common causes**
- URL or route path misspelled.
- Wrong backend base URL.
- Stale deployment or outdated client.
- Wrong host or path in request.

**How to troubleshoot**
1. Verify the base URL and route path.
2. Check documented routes for the endpoint.
3. Verify deployment is the correct version.
4. Check CDN/proxy redirect rules.
5. Test with the correct host and port.

### 405 — Method Not Allowed

**Meaning:** The URL exists but the endpoint does not support the HTTP method used.

**How to troubleshoot**
1. Check the HTTP method (GET/POST/PUT/PATCH/DELETE).
2. Verify the route accepts the method.
3. Configure allowed methods on the route (e.g., `allow_methods=["*"]`).
4. Return the proper `Allow` header.

### 406 — Not Acceptable

**Meaning:** The server cannot return a response in any format listed in the request's `Accept` header.

**How to troubleshoot**
1. Check the `Accept` header.
2. Verify supported response formats (JSON, XML, etc.).
3. Update the client to request a supported format.

### 408 — Request Timeout

**Meaning:** The request took too long and timed out.

**Common causes**
- Slow network.
- Busy backend.
- Upstream AI provider or external service slow.
- Proxy or backend timeout too short.

**How to troubleshoot**
1. Retry once after checking the network.
2. Check backend logs for slow operations.
3. Review timeout settings (`LLM_TIMEOUT_SECONDS`, proxy timeouts).
4. Avoid rapid retries.
5. Identify the slow component first.

### 409 — Conflict

**Meaning:** The request conflicts with the current resource state (e.g., duplicate record).

**How to troubleshoot**
1. Check for duplicate records.
2. Use unique constraints to prevent conflicts.
3. Return a clear conflict message.
4. Consider optimistic locking for concurrent updates.
5. Use `PUT` with conditional headers to resolve conflicts.

### 410 — Gone

**Meaning:** The resource has been intentionally removed and is no longer available.

**How to troubleshoot**
1. Confirm the resource has been retired.
2. Update clients to use the replacement route.
3. Document deprecation and removal dates.
4. Redirect to replacement endpoint if appropriate.

### 413 — Payload Too Large

**Meaning:** The request body exceeds the server or intermediary limit.

**Common causes**
- Unusually large request body.
- Long chat history.
- Proxy or platform limit exceeded.

**How to troubleshoot**
1. Reduce body size.
2. Send only the needed history.
3. Check server, proxy, and platform limits.
4. Ensure the request is below the 10 MB guard (or platform limit).

### 415 — Unsupported Media Type

**Meaning:** The `Content-Type` is not supported by the endpoint.

**How to troubleshoot**
1. Send the expected content type (e.g., `application/json`).
2. Verify the parser or upload handler is enabled.
3. Check supported MIME types in the route.

### 416 — Range Not Satisfiable

**Meaning:** The requested byte range is outside the available content.

**How to troubleshoot**
1. Check the `Range` header.
2. Verify the current file or resource size.
3. Handle the range request consistently.
4. Return a proper 416 response with `Content-Range` header.

### 424 — Failed Dependency

**Meaning:** The request failed because a dependent operation failed.

**How to troubleshoot**
1. Inspect the downstream service or dependency.
2. Return a useful error message.
3. Retry only for transient failures.
4. Log the dependency failure with correlation ID.

### 429 — Too Many Requests

**Meaning:** The client has exceeded the rate limit.

**Common causes**
- Tightly looped requests.
- Shared rate limit across clients.
- Provider applies rate limiting.

**How to troubleshoot**
1. Wait and check the `Retry-After` header.
2. Prevent duplicate submissions.
3. Review configured rate limits.
4. Use exponential backoff.
5. Debounce rapid frontend input.

### 500 — Internal Server Error

**Meaning:** An unexpected server-side failure occurred.

**Common causes**
- Unhandled exception in application code.
- Missing configuration.
- Database failure.
- Dependency error.
- Memory exhaustion.

**How to troubleshoot**
1. Check backend logs for the stack trace.
2. Verify environment variables are set correctly.
3. Reproduce with the same request/body.
4. Check for recent changes (deploy, config, dependency).
5. Never expose secrets or stack traces to end users.
6. Restrict debug mode in production.

### 502 — Bad Gateway

**Meaning:** The gateway or proxy received an invalid response from the backend or upstream service.

**Common causes**
- Backend is down or restarting.
- Wrong proxy port configured.
- Upstream service crashed.
- Backend returned an invalid or empty response.

**How to troubleshoot**
1. Verify the backend is running and healthy.
2. Test `GET /health` and inspect its reported status.
3. Review logs for upstream errors.
4. Verify the upstream address and port.
5. Check if the issue is caused by the backend host or external provider.
6. Test the backend directly on the host.

### 503 — Service Unavailable

**Meaning:** The service is temporarily unable to handle requests, but it is expected to become available after some delay.

**Common causes**

**Backend/service-side**
- The backend process is restarting, crashed, or in a crash loop.
- The hosting platform suspended or restarted the service.
- The backend is overloaded or running out of memory.
- The app failed to start due to missing required environment variables.
- The application crashed during startup (missing env var, failed DB connection, failed vector store connection).

**Knowledge base / embedding**
- `KB_ENABLED=false` or the knowledge base has not been rebuilt yet.
- `JINA_API_KEY` is missing or invalid.
- Qdrant (vector store) is unreachable or down.
- The index has not been built or has been deleted.

**LLM / AI provider**
- The LLM provider returned 503, 502, or timed out.
- Rate limit exceeded (`429`) — the provider may return 503 instead of 429 in some cases.
- The LLM model is temporarily unavailable or overloaded.
- `LLM_BASE_URL` or `LLM_MODEL` is misconfigured or the provider endpoint changed.

**Upstream / proxy**
- A reverse proxy or load balancer could not reach the backend.
- The backend returned an invalid or empty response.
- The proxy timeout is shorter than the backend's response time.

**Deploy/startup failures**
- Missing required environment variables (e.g., `JINA_API_KEY`, `KB_ENABLED`, `PORT`).
- The app crashed during startup and is in a `CrashLoopBackOff` state.
- The app is waiting for a service that is not ready (e.g., Qdrant, PostgreSQL).

**How to troubleshoot**

1. **Check backend logs** — Look for the exact error at the time of the 503.
   - `KeyError: 'JINA_API_KEY'` — missing environment variable
   - `Connection refused` to Qdrant — vector store not reachable
   - `ModuleNotFoundError` — missing Python package or wrong directory
   - `Failed to build index` — knowledge base or embedding config issue

2. **Call the health endpoint** and inspect the reported status:
   - If the response includes `status: "ok"`, the backend is alive but dependencies may be down.
   - If the response includes `status: "error"` or a dependency field is `false`, that dependency is the cause.
   - Example healthy response: `{"status": "ok", "dependencies": {"kb": true, "llm": true, "vector_store": true}}`

3. **Check knowledge base status** — Verify:
   - `enabled` is `true` (not `false` or absent)
   - Embedding configuration is present and valid
   - Vector store configuration is present
   - The index has been built successfully (build on startup or via rebuild command)

4. **Check the LLM provider** — Verify:
   - `LLM_API_KEY` is set and valid
   - `LLM_BASE_URL` is correct
   - `LLM_MODEL` is a valid model
   - The provider is not experiencing outages (check provider status page)

5. **Check the hosting platform** — For Render:
   - View the deployment logs in the dashboard
   - Check if the service is in a "restarting" or "crashed" state
   - Verify the service is not sleeping (free tier may sleep after inactivity)
   - Check the `PORT` environment variable — Render provides this dynamically
   - Review the `startCommand` in the deployment config

6. **Check for rate limiting** — The provider may be rate-limiting your account. Check:
   - Rate limit settings in the deployment config
   - LLM provider dashboard for quota usage
   - Request frequency from the frontend

7. **Retry after a delay** — 503 is a transient error. Use exponential backoff:
   - Wait 1 second, then retry once
   - If still failing, wait 5 seconds, then retry once
   - If still failing, wait 30 seconds, then retry once
   - If still failing after 3 retries, surface the error to the user with a friendly message

**Platform-specific 503 causes**
- **Free tier sleeping**: Free dynos sleep after 15 minutes of inactivity. When woken up, there may be a brief 503.
- **Build fails**: If the build fails, the service may not start, causing 503 on first request.
- **Resource limits**: Free dyno memory limits may cause crashes under load.
- **Route misconfiguration**: If the proxy points to the wrong port or host, the backend may not be reachable.

**Auto-healing checklist**
1. Check the health endpoint for dependency status.
2. Verify environment variables are set.
3. Check the deployment logs for startup errors.
4. Verify the knowledge base index was built successfully.
5. Verify the LLM provider is responding.
6. Retry after a delay.
7. If the issue persists, check the platform dashboard for service health.

**Example: How to read a 503 in the chatbot UX**
When the chatbot returns a 503 instead of a knowledge-based answer, the frontend should:
1. Show a user-friendly message: "The service is temporarily unavailable. Please wait a moment and try again."
2. Not expose internal error details (no stack traces, no API keys, no provider errors).
3. Optionally show a "Try again" button that retries with backoff.
4. If the error persists for >10 minutes, suggest contacting support.

---

### 504 — Gateway Timeout

**Meaning:** The gateway or proxy did not receive a response from the backend or upstream service in time.

**Common causes**
- The AI provider response is slow.
- The backend is waiting on a network or external-service call.
- The proxy timeout is shorter than the operation's completion time.
- The backend is overloaded.

**How to troubleshoot**
1. Check backend logs and the timing of the upstream request.
2. Review timeout settings (`LLM_TIMEOUT_SECONDS`, proxy timeout, connection pool timeouts).
3. Check the status of the configured AI provider.
4. Retry safely after a delay.
5. Do not increase timeouts blindly; first identify which component is slow.

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

---

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

### Cloud Provider Errors

#### AWS (Amazon Web Services)

**Common AWS error types:** `InvalidParameter`, `UnauthorizedOperation`, `AccessDenied`, `NotFoundException`, `LimitExceeded`

**AWS S3 errors**
- `NoSuchBucket`: Verify bucket name/region, create bucket if missing, check app configuration.
- `NoSuchKey`: Verify object key, list objects, check case sensitivity, verify upload key.
- `AccessDenied`: Check bucket policy, IAM policy for `s3:GetObject`/`s3:PutObject`, check bucket ACL, check CORS if browser access.

**AWS Lambda errors**
- `InvalidParameterValueException`: Check error for invalid parameter, verify runtime version, adjust timeout/memory, verify execution role, check deployment package size (10 MB unzipped).
- `TooManyRequestsException`: Check concurrency limit, reduce invocation rate or add jitter, request concurrency increase, use async invocation with backoff.

**AWS DynamoDB errors**
- `ProvisionedThroughputExceededException`: Check CloudWatch metrics, add auto-scaling or increase capacity, use on-demand for unpredictable workloads, distribute keys, implement backoff with jitter.
- `ConditionalCheckFailedException`: Verify item exists and attribute value correct, check condition expression, use `Expected` carefully (case-sensitive), retry with fresh read for optimistic locking.

**AWS API Gateway errors**
- `4XX` / `Unauthorized` / `Access Denied`: Check authorization type (Lambda authorizer, IAM, Cognito, API key), verify token/secret, check IAM policy, verify request headers (`x-api-key`), check throttling settings.
- `429` / `Too Many Requests`: Check throttling settings, check account-level limits, implement exponential backoff with jitter, use API keys with higher limits, prevent duplicate submissions.

**AWS Cognito errors**
- `NotAuthorizedException`: Verify password/username, check user is not blocked, verify token is not expired, use refresh token, check MFA status.
- `TooManyRequestsException`: Reduce request rate, implement exponential backoff, check for duplicate auth requests, request rate limit increase, use token cache.

**AWS general errors**
- `InvalidParameter` / `InvalidParameterValue`: Read error for parameter name/constraint, verify against API docs, check for typos/missing fields, validate value format (ARN, date, region).
- `UnauthorizedOperation`: Read denied action/resource, check IAM policy, verify role trust policy, verify resource ARN (region, account), test with `aws iam simulate-principal-policy`.
- `AccessDenied`: Verify credentials (`aws sts get-caller-identity`), check IAM policy, check resource policy, verify credentials not expired/revoked, check temporary credentials.
- `NotFoundException` / `Resource not found`: Verify resource ID/ARN, list resource (AWS console), check region/account, verify correct environment.

#### GCP (Google Cloud Platform)

**Common GCP error types:** `StorageException`, `PermissionDenied`, `QueryJobError`, `FirebaseAuthError`

**GCP Cloud Storage errors**
- `Not found` / `StorageException`: Verify bucket/object, list objects (`gsutil ls`), check case sensitivity, verify upload path.
- `PermissionDenied`: Check IAM policy for bucket/object, verify service account has required role, check credentials scope, verify public access is not intended.

**GCP BigQuery errors**
- `QueryJobError` / `Query exceeded limit`: Check estimated bytes processed, use `LIMIT` or table scanner, use partition filters, request higher budget or on-demand, cache results.

**GCP Firebase errors**
- `The link is invalid or it has expired`: Verify link not expired (up to 30 days), check link parameters, regenerate link, check Firebase console for analytics.

#### Azure (Microsoft Azure)

**Common Azure error types:** `AuthenticationFailed`, `BlobNotFoundException`

**Azure Blob Storage errors**
- `The specified blob does not exist`: Verify container/blob names, list blobs (`az storage blob list`), check case sensitivity, verify upload path.
- `AuthenticationFailed`: Verify connection string/account key, check credentials not expired/regenerated, verify account name, check service principal credentials/scope.

---

### General Cloud Provider Troubleshooting

**1. Authentication / Authorization**
- Verify credentials are set and non-empty.
- Check credentials are not expired or revoked.
- Verify the correct IAM role/service account is attached.
- Check the resource ARN, region, and account match.

**2. Permissions / Policy**
- Read the exact denied action/resource from the error.
- Check IAM policy for Allow vs Deny effects.
- Verify the service account or role has the minimum required permission (least privilege).
- Test with `aws iam simulate-principal-policy` (AWS) or `gcloud auth` (GCP).

**3. Rate Limits**
- Most cloud providers return `429` or `TooManyRequestsException`.
- Implement exponential backoff with jitter.
- Use API keys with higher limits if available.
- Check account-level limits in the provider console.

**4. Quota / Limit Exceedance**
- Read the error for the specific limit exceeded.
- Request quota increase via the provider's service quota console.
- Reduce request rate or use multiple resources (auto-scaling).

**5. Region / Availability Zone**
- Verify the resource is in the correct region and account.
- Check cross-region access restrictions.
- Ensure the service is running in the expected availability zone.

**6. Network / Firewall**
- Verify security groups, firewall rules, and network ACLs allow traffic.
- Check outbound internet access for API calls.
- Verify VPC endpoints or NAT gateway configuration.
- Test connectivity from the instance to the provider API endpoint.

---

## Safe Troubleshooting Rules

- Record the endpoint, timestamp, HTTP status code, and request ID if available.
- Check the response body and server logs before assuming the cause.
- Never share API keys, admin tokens, passwords, or unredacted secrets.
- Do not expose stack traces or internal implementation details to end users.
- Retry only temporary failures, and use backoff for repeated requests.
- Treat this document as general guidance; confirm exact behaviour against the deployed application.
