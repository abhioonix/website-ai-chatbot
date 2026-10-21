"""In-memory, per-client-IP rate limiting.

Deliberately dependency-free: the app runs as a single process on the free
hosting tier, so a shared store (Redis) is not required. Counts reset on
redeploy, which is acceptable for a prototype.
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field

from fastapi import Request


@dataclass
class _Window:
    hits: deque = field(default_factory=lambda: deque())


class RateLimitExceeded(Exception):
    """Raised when a client exceeds the request budget."""


class RateLimiter:
    """Fixed-window limiter keyed by client IP."""

    def __init__(self, limit_per_minute: int) -> None:
        self.limit = max(1, limit_per_minute)
        self.window_seconds = 60
        self._clients: dict[str, _Window] = defaultdict(_Window)
        self._lock = threading.Lock()

    def check(self, client: str) -> tuple[bool, dict]:
        """Return (allowed, metadata). Metadata is safe to expose."""
        now = time.monotonic()
        cutoff = now - self.window_seconds

        with self._lock:
            window = self._clients[client]
            while window.hits and window.hits[0] <= cutoff:
                window.hits.popleft()

            if len(window.hits) >= self.limit:
                retry_after = int(self.window_seconds - (now - window.hits[0])) + 1
                return False, {"limit": self.limit, "retry_after": max(1, retry_after)}

            window.hits.append(now)
            remaining = self.limit - len(window.hits)
            return True, {"limit": self.limit, "remaining": remaining}

    def prune(self, now: float | None = None) -> None:
        """Drop idle clients so the dict does not grow unbounded."""
        now = now if now is not None else time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            for client in [c for c, w in self._clients.items() if not w.hits or w.hits[-1] <= cutoff]:
                self._clients.pop(client, None)


def client_ip(request: Request) -> str:
    """Best-effort client IP, honouring a single proxy hop.

    Behind Render's proxy the left-most `X-Forwarded-For` entry is the client.
    """
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"
