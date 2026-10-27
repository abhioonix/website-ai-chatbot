# Backend Troubleshooting — Node.js and Express

This document covers Node.js/Express-specific application errors. Adapt the patterns here to your project structure.

---

## npm install fails

**Cause:** Missing dependencies, version mismatch, or corrupted install.

**Fix:**
1. Clear cache: `npm cache clean --force`.
2. Delete `node_modules` and `package-lock.json`, then run `npm install`.
3. Check Node version matches `package.json` `engines` field.
4. Use `nvm` to switch versions.
5. If native modules fail: `npm rebuild` or install build tools (`build-essential` on Linux).

---

## EADDRINUSE: port already in use

**Cause:** Another process holds the port.

**Fix:**
1. Find the process: `lsof -i :3000` (Linux/Mac) or `netstat -ano | findstr :3000` (Windows).
2. Kill the process or change the `PORT` environment variable.

---

## Cannot find module

**Cause:** Dependencies not installed, wrong path, or CommonJS/ESM mismatch.

**Fix:**
1. Run `npm install`.
2. Verify `require()` or `import` paths are relative (`./`) for local files.
3. For ES modules, ensure `"type": "module"` is set in `package.json`.
4. For dynamic imports, wrap in `async` function and use `await import()`.

---

## Common Node.js error codes

| Code | Name | Fix |
|---|---|---|
| EADDRINUSE | Port already in use | Change port or kill process |
| ECONNREFUSED | Connection refused | Verify target service running, check host/port |
| ENOTFOUND | DNS lookup failed | Check domain, DNS config, firewall |
| ETIMEDOUT | Connection timed out | Check network, provider status, increase timeout |
| EPERM | Permission denied | Check file permissions, run with correct user |
| EACCES | Permission denied | Check file/dir permissions, sudo not needed in production |
| ENOENT | No such file or directory | Verify path, check file exists |
| EISDIR | Is a directory | Use fs.readFileSync for files, not directories |
| EMFILE | Too many open files | Increase limit, close handles, fix leaks |
| ENONET | No such network path | Check network, DNS, verify path/URL |
| EHOSTUNREACH | Host unreachable | Check network, firewall, VPN |
| EPROTO | Protocol error | Check protocol version, TLS config, HTTP version |

---

## Express-specific

**Cause:** Middleware order, routing, or error handling issues.

**Fix:**
1. **Middleware order:** Register parsers (`express.json()`) before routes that read `req.body`.
2. **Error handling:** Register 4-argument error handlers (`err, req, res, next`) LAST, after routes.
3. **Async routes:** Use `try/catch` or a wrapper; pass errors to `next()`.
4. **CORS:** Use the `cors` middleware before routes that need it, with specific origins in production.

---

## CORS in Express

**Fix:**
```javascript
const cors = require("cors");
app.use(cors({
  origin: "https://your-frontend.com",  // specific origin, not wildcard
  credentials: true,
}));
```

**Production advice:** Use specific origins. Credentialed requests cannot use wildcard origins. The browser client must be configured to send credentials where required.

---

## Environment variables

**Cause:** Missing or misnamed env vars.

**Fix:**
1. Use `process.env.VAR_NAME` to read config.
2. For local `.env` files, use `dotenv`: `require("dotenv").config()`.
3. Never commit `.env` files or secrets.
4. Verify env vars in production (platform dashboard, Docker `--env` flag).

---

## Nodemon not restarting

**Fix:**
1. Check `nodemon.json` ignore/watch patterns.
2. Verify changed file is within watched paths.
3. Check filesystem watcher limits (`fs.inotify.max_user_watches`).
4. Type `rs` in the Nodemon terminal to restart manually.

---

## Common Express error codes

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

## Debugging

**Fix:**
1. **Logging:** Use `console.error` or a logger (winston, pino) with levels.
2. **Stack traces:** Read bottom-up; the last frame is where the error originated.
3. **Breakpoints:** Use VS Code debugger, Chrome DevTools, or `node --inspect`.
4. **Process manager:** Use `pm2` for auto-restart: `pm2 start app.js --name api`.
5. **Health check:** Expose `/health` for load balancer and container orchestrator probes.
