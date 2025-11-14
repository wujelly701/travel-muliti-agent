"""Structured JSON logger.
Ref: §5 错误与日志规范
"""
from __future__ import annotations
import json, sys, time, uuid
from datetime import datetime
from .error_tracker import ERROR_TRACKER

def _emit(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")

def log(level: str, stage: str, message: str, *, session_id: str | None = None, code: str | None = None, extra: dict | None = None, start_ts: float | None = None, trace_id: str | None = None) -> None:
    now = datetime.utcnow().isoformat()
    base = {
        "timestamp": now,
        "level": level.upper(),
        "stage": stage,
        "message": message,
    }
    if session_id:
        base["session_id"] = session_id
    if code:
        base["code"] = code
    if start_ts is not None:
        base["latency_ms"] = int((time.time() - start_ts) * 1000)
    if trace_id:
        base["trace_id"] = trace_id
    if extra:
        base.update(extra)
    _emit(base)

def log_info(stage: str, message: str, **kw):
    log("INFO", stage, message, **kw)

def log_error(stage: str, message: str, **kw):
    code = kw.get("code")
    session_id = kw.get("session_id")
    ERROR_TRACKER.record(code, stage, session_id, message)
    log("ERROR", stage, message, **kw)

def log_warn(stage: str, message: str, **kw):
    log("WARN", stage, message, **kw)

def new_trace_id() -> str:
    return uuid.uuid4().hex[:12]
