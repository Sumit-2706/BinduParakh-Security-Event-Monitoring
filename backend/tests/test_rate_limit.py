"""
Tests for the in-process rate limiter (app/rate_limit.py).

FastAPI's `rate_limit(...)` helper returns a dependency that enforces a
per-IP sliding window. These tests drive both the generated dependency and
the internal limiter directly, so they run without a server or database.
"""
import time

import pytest
from fastapi import HTTPException

from app.rate_limit import rate_limit, _SlidingWindowLimiter


def _fake_request(ip: str) -> type:
    host = type("_Client", (), {"host": ip})()
    req = type("_Request", (), {})()
    req.client = host
    return req


def test_blocks_after_max_hits():
    dep = rate_limit(max_hits=3, window_seconds=60)
    req = _fake_request("1.2.3.4")
    for _ in range(3):
        dep(req)
    with pytest.raises(HTTPException) as exc:
        dep(req)
    assert exc.value.status_code == 429


def test_different_ips_have_independent_buckets():
    dep = rate_limit(max_hits=2, window_seconds=60)
    req_a = _fake_request("10.0.0.1")
    req_b = _fake_request("10.0.0.2")
    for _ in range(2):
        dep(req_a)
    with pytest.raises(HTTPException):
        dep(req_a)
    dep(req_b)  # a fresh IP is still allowed


def test_stale_keys_are_pruned(monkeypatch):
    """Once the key table grows past the prune threshold, keys whose last
    hit fell out of the window must be dropped -- otherwise the in-process
    dict grows forever on a long-running deployment."""
    limiter = _SlidingWindowLimiter(max_hits=20, window_seconds=60)
    fake_time = {"now": 1000.0}
    monkeypatch.setattr(time, "time", lambda: fake_time["now"])

    for i in range(5000):
        limiter.allow(f"ip-{i}")
    assert len(limiter._hits) == 5000

    # Advance beyond the window, then trigger a prune with one new key.
    fake_time["now"] += 120.0
    limiter.allow("fresh-ip")
    assert len(limiter._hits) == 1