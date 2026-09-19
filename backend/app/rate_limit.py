"""
Minimal in-process rate limiter (sliding window) used to protect the
auth / ingest endpoints from brute force and spam.

Deliberately dependency-free: a per-process dict + lock is plenty for a
self-hosted app. If you ever scale to many workers behind a load balancer,
swap this for a shared store (Redis) -- the interface stays the same
(rate_limit(...) returns a FastAPI dependency).
"""
import threading
import time
from typing import Callable

from fastapi import HTTPException, Request


# When the key table exceeds this many entries, drop every key whose last
# hit already fell out of the window. Keeps the in-process dict bounded
# under normal traffic without a background thread or timers.
_PRUNE_AFTER = 4096


class _SlidingWindowLimiter:
    def __init__(self, max_hits: int, window_seconds: float):
        self.max_hits = max_hits
        self.window_seconds = window_seconds
        self._hits: dict = {}
        self._lock = threading.Lock()

    def _prune_stale(self, window_start: float) -> None:
        """Drops keys whose most recent hit is older than the window, so a
        long-running process doesn't accumulate an entry per distinct IP
        forever (unbounded memory growth otherwise)."""
        self._hits = {
            k: v for k, v in self._hits.items()
            if v and v[-1] > window_start
        }

    def allow(self, key: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds
        with self._lock:
            if len(self._hits) > _PRUNE_AFTER:
                self._prune_stale(window_start)
            recent = [t for t in self._hits.get(key, []) if t > window_start]
            if len(recent) >= self.max_hits:
                self._hits[key] = recent
                return False
            recent.append(now)
            self._hits[key] = recent
            return True


def rate_limit(max_hits: int = 20, window_seconds: float = 60) -> Callable:
    """Returns a FastAPI dependency that rejects a caller's IP once it
    exceeds `max_hits` requests per `window_seconds`. Because FastAPI
    caches the callable for each route, the returned dependency shares one
    limiter instance across every request to that route."""
    limiter = _SlidingWindowLimiter(max_hits, window_seconds)

    def dependency(request: Request) -> None:
        key = request.client.host if request.client else "unknown"
        if not limiter.allow(key):
            raise HTTPException(
                status_code=429,
                detail="Too many requests -- wait a moment and try again.",
            )

    return dependency