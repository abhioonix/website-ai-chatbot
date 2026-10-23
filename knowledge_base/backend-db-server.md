# Backend Troubleshooting — Databases and Servers

## Connection refused to database

Database not running or wrong host/port. Check service status: systemctl status postgresql. Verify connection string (host, port, db name, user, password). For Docker, use container name as host, not localhost.

## Authentication failed

Wrong username/password or user lacks privileges. Check .env values. Create user with proper grants: GRANT ALL PRIVILEGES ON db.* TO 'user'@'%';

## Connection pool exhausted

Too many open connections. Set pool size and max overflow in SQLAlchemy/Prisma. Always close sessions (use context managers or yield dependencies). Check for connection leaks (sessions not closed on errors).

## Migration errors

Alembic/Prisma migrate fails on schema drift. Run alembic revision --autogenerate then upgrade head. For conflicts, create a merge migration. Never edit applied migrations.

## CORS + cookies

For credentialed requests, set allow_credentials=True and specific origins (not wildcard). Frontend must send credentials: 'include'. Cookie needs SameSite/Secure flags for cross-site.

## Port binding / permission denied

Ports below 1024 require root. Use 8000/3000 or run behind nginx. "Address already in use" — kill the process or change port.

## 500 Internal Server Error

Check server logs (terminal where uvicorn/node runs). Common causes: unhandled exception, missing env var, DB connection failure. Enable debug mode only in dev. Add try/except around route handlers and log the traceback.

## Nginx 502 Bad Gateway

Upstream (app) not running or wrong proxy_pass port. Check app logs and that the app listens on the expected port. Verify nginx config with nginx -t.

## SSL/TLS errors

Certificate expired or mismatched. Renew with certbot. Ensure full chain is served. For local dev use mkcert.

## Docker container exits immediately

Check logs: docker logs <container>. Usually missing CMD, crash on startup, or missing env. Run interactively: docker run -it image bash.

## Process management

Use systemd or pm2 for auto-restart. pm2 start app.js --name api. Enable on boot: pm2 startup && pm2 save.
