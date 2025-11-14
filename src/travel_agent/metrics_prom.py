"""Prometheus metrics registry wrapping internal METRICS.
Exports counters/histogram for scraping.
"""
from __future__ import annotations
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

PLAN_REQUESTS = Counter("plan_requests_total", "Total plan requests")
CLARIFY_SESSIONS = Counter("clarify_sessions_total", "Clarify sessions started")
CLARIFY_ROUNDS = Counter("clarify_rounds_total", "Additional clarify rounds")
CLARIFY_QUESTIONS = Counter("clarify_questions_total", "Total clarify questions issued")
WORKFLOWS_COMPLETED = Counter("workflows_completed_total", "Completed workflows")
WORKFLOW_LATENCY = Histogram("workflow_latency_ms", "Workflow end-to-end latency (ms)")
LLM_CALLS = Counter("llm_calls_total", "LLM calls attempted")
LLM_ERRORS = Counter("llm_errors_total", "LLM errors")
LLM_FALLBACKS = Counter("llm_fallbacks_total", "LLM fallbacks invoked")
RESULT_CACHE_HITS = Counter("result_cache_hits_total", "Result cache hits")
RESULT_CACHE_MISSES = Counter("result_cache_misses_total", "Result cache misses")

def export_prometheus() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST

__all__ = [
    "PLAN_REQUESTS","CLARIFY_SESSIONS","CLARIFY_ROUNDS","CLARIFY_QUESTIONS",
    "WORKFLOWS_COMPLETED","WORKFLOW_LATENCY","LLM_CALLS","LLM_ERRORS","LLM_FALLBACKS","RESULT_CACHE_HITS","RESULT_CACHE_MISSES","export_prometheus"
]