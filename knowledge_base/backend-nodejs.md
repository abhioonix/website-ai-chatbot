# Backend Troubleshooting — Node.js and Express

## npm install fails

Clear cache: `npm cache clean --force`. Delete `node_modules` and `package-lock.json`, then `npm install`. Check Node version matches package `engines`. Use `nvm` to switch versions.

## EADDRINUSE: port already in use

Another process holds the port. Find it: `lsof -i :3000` (Linux/Mac) or `netstat -ano | findstr :3000` (Windows). Kill it or change `PORT` env var.

## Cannot find module

Node resolves modules from `node_modules` relative to the file. Run `npm install`. Check `require`/`import` paths are relative (`./`) for local files. For ES modules use `"type": "module"` in `package.json`.

## Additional Node.js / Express Errors

### Express middleware order
Middleware executes in registration order. Register parsers (`express.json()`) before routes that read `req.body`. Register error-handling middleware (4 args) after the routes/middleware whose errors it handles.

### CORS in Express
Install/configure the `cors` middleware before routes that need it. Example for local frontend:
```javascript
const cors = require("cors");
app.use(cors({
  origin: "http://localhost:3000",
  credentials: true,
}));
```
Use the real frontend origin(s) in production. Credentialed requests cannot use `Access-Control-Allow-Origin: *`. The browser client must be configured to send credentials where required.

### Unhandled promise rejection / async route errors
Always catch rejected promises. Use `try/catch` and pass failures to Express error middleware, or use a wrapper compatible with your Express version. Don't rely on unhandled rejections as an error-handling strategy.

### Environment variables in Node
Read configuration with `process.env.NAME`. For local `.env` files, use `dotenv`: `require("dotenv").config()` (CommonJS) or the corresponding ES module import. Never commit `.env` files or secrets.

### Nodemon does not restart
Check `nodemon.json` ignore/watch patterns, confirm the changed file is within watched paths, and check filesystem watcher limits (`fs.inotify.max_user_watches`). Type `rs` in the Nodemon terminal to restart manually.

### `EPERM` or symlink errors on external drives
Some filesystems (exFAT/NTFS) lack symlink support. Move the project to the internal ext4 filesystem and run npm there.

### Express `ENOENT` / "Cannot find module"
**Cause:** A dependency is not installed, a local path is wrong, or CommonJS/ES-module settings don't match.
**Fix:** Install dependencies, verify local imports use relative paths (`./`) where needed, check `package.json` module config. For ES modules, set `"type": "module"` in `package.json`.

### Express rate limiting
**Fix:** Use `express-rate-limit`. Choose keys and limits per your threat model (IP or authenticated user), return `429` when a client exceeds its rate, include `Retry-After` header, configure trusted proxy handling so client IPs can't be spoofed.

### Express error handling middleware
**Fix:** Register error-handling middleware (4 args: `err, req, res, next`) LAST, after routes and other middleware. Use `try/catch` in async handlers or a wrapper. Don't rely on unhandled rejections.

### Node.js `ETIMEDOUT`
**Cause:** A network call or operation timed out.
**Fix:** Check upstream health, database query plans, external API calls, app logs, and proxy/app timeout settings. Fix underlying latency before increasing timeouts indiscriminately.

### Node.js `ECONNREFUSED`
**Cause:** The server could not connect to a service.
**Fix:** Verify the target service is running, check host/port in config, check firewall rules, for Docker use container/service name as host.
