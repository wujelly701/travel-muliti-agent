"""Per-session sliding window rate limiter (in-memory).
Fallback simple implementation for MVP; can be swapped with Redis scripts later.
"""
from __future__ import annotations
import time
from collections import deque
from typing import Deque, Dict
from .config import RATE_LIMIT_REQUESTS_PER_MIN, RATE_LIMIT_WINDOW_SECONDS

_REQUESTS: Dict[str, Deque[float]] = {}

def rate_limit_allow(session_id: str) -> bool:
    now = time.time()
    window = RATE_LIMIT_WINDOW_SECONDS
    limit = RATE_LIMIT_REQUESTS_PER_MIN
    dq = _REQUESTS.get(session_id)
    if dq is None:
        dq = deque()
        _REQUESTS[session_id] = dq
    # purge old
    while dq and now - dq[0] > window:
        dq.popleft()
    if len(dq) >= limit:
        return False
    dq.append(now)
    return True

def rate_limit_peek(session_id: str) -> int:
    dq = _REQUESTS.get(session_id)
    return len(dq) if dq else 0

__all__ = ["rate_limit_allow", "rate_limit_peek"]