# Backend Troubleshooting — Node.js and Express

## npm install fails

Clear cache: npm cache clean --force. Delete node_modules and package-lock.json, then npm install. Check Node version matches package engines. Use nvm to switch versions.

## EADDRINUSE port already in use

Another process holds the port. Find it: lsof -i :3000 (Linux/Mac) or netstat -ano | findstr :3000 (Windows). Kill it or change PORT env var.

## Cannot find module

Node resolves modules from node_modules relative to the file. Run npm install. Check require/import paths are relative (./) for local files. For ES modules use "type": "module" in package.json.

## Express middleware order

Middleware runs in registration order. Register body parsers (express.json()) before routes. Error-handling middleware (4 args) must be registered last.

## CORS in Express

Use cors package: app.use(cors({ origin: "http://localhost:3000", credentials: true })). Place before routes.

## Unhandled promise rejection

Always catch async errors. Use try/catch in async route handlers or a wrapper like express-async-errors. Unhandled rejections crash Node 15+.

## Environment variables in Node

Use process.env.VAR. Load .env with dotenv: require('dotenv').config(). Never commit .env.

## Nodemon not restarting

Check nodemon.json ignore patterns. Restart manually with rs in nodemon prompt. Ensure file watcher limits aren't exceeded (Linux: fs.inotify.max_user_watches).

## EPERM on npm (external drives)

exFAT/NTFS drives lack symlink support. Move project to internal ext4 filesystem and run npm there.
