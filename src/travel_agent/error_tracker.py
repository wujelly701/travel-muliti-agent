"""Recent error tracker (ring buffer) for diagnostics.
Stores last N errors with timestamp, code, stage, session_id, message.
Endpoint will expose snapshot; metrics already count totals.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List
from threading import Lock
from datetime import datetime

@dataclass
class ErrorRecord:
    ts: datetime
    code: Optional[str]
    stage: str
    session_id: Optional[str]
    message: str

class ErrorTracker:
    def __init__(self, capacity: int = 200):
        self._lock = Lock()
        self._cap = capacity
        self._records: List[ErrorRecord] = []

    def record(self, code: Optional[str], stage: str, session_id: Optional[str], message: str):
        rec = ErrorRecord(datetime.utcnow(), code, stage, session_id, message)
        with self._lock:
            self._records.append(rec)
            if len(self._records) > self._cap:
                # drop oldest
                self._records = self._records[-self._cap:]

    def snapshot(self, limit: Optional[int] = None, since_seconds: Optional[int] = None):
        with self._lock:
            items = list(self._records)
        if since_seconds is not None:
            cutoff = datetime.utcnow().timestamp() - since_seconds
            items = [r for r in items if r.ts.timestamp() >= cutoff]
        if limit is not None:
            items = items[-limit:]
        return [
            {
                "ts": r.ts.isoformat(),
                "code": r.code,
                "stage": r.stage,
                "session_id": r.session_id,
                "message": r.message,
            }
            for r in items
        ]

ERROR_TRACKER = ErrorTracker()

__all__ = ["ERROR_TRACKER"]