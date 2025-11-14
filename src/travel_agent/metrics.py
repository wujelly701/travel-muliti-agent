"""Simple in-memory metrics collection for MVP."""
from __future__ import annotations
from dataclasses import dataclass
from threading import Lock
from typing import Dict

@dataclass
class _MetricsState:
    plan_requests: int = 0
    clarify_sessions: int = 0
    clarify_rounds: int = 0
    clarify_questions: int = 0
    workflow_completed: int = 0
    workflow_latency_total_ms: float = 0.0
    workflow_latency_count: int = 0
    llm_calls: int = 0
    llm_errors: int = 0
    llm_fallbacks: int = 0
    cache_hits: int = 0
    cache_misses: int = 0

try:
    from .metrics_prom import (
        PLAN_REQUESTS, CLARIFY_SESSIONS, CLARIFY_ROUNDS, CLARIFY_QUESTIONS,
        WORKFLOWS_COMPLETED, WORKFLOW_LATENCY, LLM_CALLS, LLM_ERRORS, LLM_FALLBACKS,
        RESULT_CACHE_HITS, RESULT_CACHE_MISSES
    )
except Exception:  # pragma: no cover
    PLAN_REQUESTS = CLARIFY_SESSIONS = CLARIFY_ROUNDS = CLARIFY_QUESTIONS = WORKFLOWS_COMPLETED = WORKFLOW_LATENCY = LLM_CALLS = LLM_ERRORS = LLM_FALLBACKS = RESULT_CACHE_HITS = RESULT_CACHE_MISSES = None

class Metrics:
    def __init__(self):
        self._lock = Lock()
        self._s = _MetricsState()

    def inc_plan(self):
        with self._lock:
            self._s.plan_requests += 1
        if PLAN_REQUESTS:
            PLAN_REQUESTS.inc()

    def inc_clarify_session(self):
        with self._lock:
            self._s.clarify_sessions += 1
        if CLARIFY_SESSIONS:
            CLARIFY_SESSIONS.inc()

    def add_clarify_questions(self, n: int):
        with self._lock:
            self._s.clarify_questions += n
        if CLARIFY_QUESTIONS:
            CLARIFY_QUESTIONS.inc(n)

    def inc_clarify_round(self):
        with self._lock:
            self._s.clarify_rounds += 1
        if CLARIFY_ROUNDS:
            CLARIFY_ROUNDS.inc()

    def record_workflow_latency(self, ms: float):
        with self._lock:
            self._s.workflow_completed += 1
            self._s.workflow_latency_total_ms += ms
            self._s.workflow_latency_count += 1
        if WORKFLOWS_COMPLETED:
            WORKFLOWS_COMPLETED.inc()
        if WORKFLOW_LATENCY:
            WORKFLOW_LATENCY.observe(ms)

    def llm_call(self):
        with self._lock:
            self._s.llm_calls += 1
        if LLM_CALLS:
            LLM_CALLS.inc()

    def llm_error(self):
        with self._lock:
            self._s.llm_errors += 1
        if LLM_ERRORS:
            LLM_ERRORS.inc()

    def llm_fallback(self):
        with self._lock:
            self._s.llm_fallbacks += 1
        if LLM_FALLBACKS:
            LLM_FALLBACKS.inc()

    def cache_hit(self):
        with self._lock:
            self._s.cache_hits += 1
        if RESULT_CACHE_HITS:
            RESULT_CACHE_HITS.inc()

    def cache_miss(self):
        with self._lock:
            self._s.cache_misses += 1
        if RESULT_CACHE_MISSES:
            RESULT_CACHE_MISSES.inc()

    def snapshot(self) -> Dict:
        with self._lock:
            avg_latency = (self._s.workflow_latency_total_ms / self._s.workflow_latency_count) if self._s.workflow_latency_count else 0.0
            return {
                "plan_requests": self._s.plan_requests,
                "clarify_sessions": self._s.clarify_sessions,
                "clarify_rounds": self._s.clarify_rounds,
                "clarify_questions": self._s.clarify_questions,
                "workflows_completed": self._s.workflow_completed,
                "workflow_avg_latency_ms": round(avg_latency, 2),
                "llm_calls": self._s.llm_calls,
                "llm_errors": self._s.llm_errors,
                "llm_fallbacks": self._s.llm_fallbacks,
                "cache_hits": self._s.cache_hits,
                "cache_misses": self._s.cache_misses,
            }

    def reset(self):  # for tests
        with self._lock:
            self._s = _MetricsState()

METRICS = Metrics()

class _ParallelMetrics:
    def __init__(self):
        self._lock = Lock()
        self.parallel_runs = 0
    def inc_parallel(self):
        with self._lock:
            self.parallel_runs += 1
    def snapshot(self):
        with self._lock:
            return {"parallel_runs": self.parallel_runs}

METRICS_PARALLEL = _ParallelMetrics()

__all__ = ["METRICS", "METRICS_PARALLEL"]