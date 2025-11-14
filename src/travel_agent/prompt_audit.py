"""LLM prompt audit ring buffer.
Captures prompt metadata, model, response stats, repair attempts, fallback usage, error codes.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List, Dict
from threading import Lock
from datetime import datetime

@dataclass
class AuditRecord:
    ts: datetime
    model: str
    prompt_tag: str
    prompt_len: int
    response_len: int
    json_valid: bool
    repair_attempts: int
    fallback_used: bool
    error_code: Optional[str]

class PromptAudit:
    def __init__(self, capacity: int = 300):
        self._lock = Lock()
        self._cap = capacity
        self._records: List[AuditRecord] = []

    def record(self, *, model: str, prompt_tag: str, prompt: str, response: str,
               json_valid: bool, repair_attempts: int, fallback_used: bool, error_code: Optional[str]):
        rec = AuditRecord(datetime.utcnow(), model, prompt_tag, len(prompt), len(response), json_valid, repair_attempts, fallback_used, error_code)
        with self._lock:
            self._records.append(rec)
            if len(self._records) > self._cap:
                self._records = self._records[-self._cap:]

    def snapshot(self, limit: int = 50, since_seconds: Optional[int] = None) -> List[Dict]:
        with self._lock:
            items = list(self._records)
        if since_seconds is not None:
            cutoff = datetime.utcnow().timestamp() - since_seconds
            items = [r for r in items if r.ts.timestamp() >= cutoff]
        items = items[-limit:]
        return [
            {
                "ts": r.ts.isoformat(),
                "model": r.model,
                "prompt_tag": r.prompt_tag,
                "prompt_len": r.prompt_len,
                "response_len": r.response_len,
                "json_valid": r.json_valid,
                "repair_attempts": r.repair_attempts,
                "fallback_used": r.fallback_used,
                "error_code": r.error_code,
            }
            for r in items
        ]

PROMPT_AUDIT = PromptAudit()

__all__ = ["PROMPT_AUDIT"]