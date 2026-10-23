# Backend Authentication Issues

## 401 Unauthorized with valid token
Cause: token expired or wrong secret.
Fix: verify JWT secret and expiry; refresh token.

## 403 Forbidden
Cause: missing permission/scope.
Fix: check RBAC and route guards.

## Session expired
Cause: cookie max-age.
Fix: extend session or re-login.