"""FastAPI endpoints for MVP.
Ref: §6 REST API 接口详细规格
"""
from __future__ import annotations
from fastapi import FastAPI, Depends, HTTPException, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from .models import ApiResponse, PlanningResult, ErrorInfo
from .workflow import workflow_run, continue_workflow, orchestrate_parallel
from .graph_workflow import run_graph
from .intent import intent_parse, intent_generate_questions, intent_apply_answers, intent_find_gaps
from .logger import log_info, log_error, new_trace_id
import time
from .models import TripIntent
from .config import REDIS_URL
from . import config as cfg
import jwt, datetime
from .session_store import create_session_store
from .errors import DomainError
from .metrics import METRICS
from .metrics_prom import export_prometheus
from .error_tracker import ERROR_TRACKER
from .prompt_audit import PROMPT_AUDIT
from .cache_util import cache_get, cache_put
from .rate_limit import rate_limit_allow

app = FastAPI(title="Travel Agent MVP")

# Adaptive session store (Redis if available, else in-memory)
_STORE = create_session_store(REDIS_URL)

class PlanRequest(BaseModel):
    session_id: str
    text: str

class ClarifyAnswer(BaseModel):
    question_id: str
    field: str
    value: str

class ClarifyRequest(BaseModel):
    session_id: str
    answers: list[ClarifyAnswer]

class DebugIntentRequest(BaseModel):
    session_id: str
    text: str

def require_auth(request: Request):
    """Auth dependency supporting API Key OR JWT (when enabled).
    Order:
    1. If JWT_ENABLE true and Authorization Bearer valid -> ok.
    2. Else if API_KEY configured and matches header -> ok.
    3. Else if neither configured -> open mode.
    4. Otherwise 401.
    """
    # JWT path
    if cfg.JWT_ENABLE:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header[7:].strip()
            try:
                payload = jwt.decode(token, cfg.AUTH_JWT_SECRET, algorithms=[cfg.AUTH_JWT_ALG])
                # simple expiry + subject check
                if "sub" not in payload:
                    raise HTTPException(status_code=401, detail="Invalid token")
                return True
            except jwt.PyJWTError:
                raise HTTPException(status_code=401, detail="Invalid or expired token")
    # API key path
    api_key = cfg.API_KEY
    if api_key:
        provided = request.headers.get("X-API-Key")
        if provided != api_key:
            raise HTTPException(status_code=401, detail="Invalid or missing API key")
        return True
    # Open mode
    return True

@app.post("/api/mvp/plan", response_model=ApiResponse)
def post_plan(req: PlanRequest, _: bool = Depends(require_auth)):
    trace_id = new_trace_id()
    start_ts = time.time()
    log_info("api", "plan_request", session_id=req.session_id, trace_id=trace_id)
    METRICS.inc_plan()
    # Rate limit check
    if not rate_limit_allow(req.session_id):
        log_error("rate_limit", "exceeded", session_id=req.session_id, code="RATE_LIMIT_EXCEEDED", trace_id=trace_id)
        return ApiResponse(success=False, error=ErrorInfo(code="RATE_LIMIT_EXCEEDED", message="Too many requests"))
    try:
        intent = intent_parse(req.text, req.session_id)
        log_info("api", "intent_parsed", session_id=req.session_id, trace_id=trace_id, extra={
            "destination": intent.destination,
            "days": intent.days,
            "budget_total": intent.budget_total,
            "depart_date": str(intent.depart_date) if intent.depart_date else None,
        })
    except DomainError as de:
        log_error("intent_parse", de.message, session_id=req.session_id, code=de.code, trace_id=trace_id)
        return ApiResponse(success=False, error=ErrorInfo(code=de.code, message=de.message))
    gaps = intent_find_gaps(intent)
    if not gaps:
        cached = cache_get(intent)
        if cached:
            METRICS.cache_hit()
            log_info("cache", "hit", session_id=req.session_id, trace_id=trace_id)
            return ApiResponse(success=True, data=cached)
        else:
            METRICS.cache_miss()
    if gaps:
        questions = intent_generate_questions(gaps)
        METRICS.inc_clarify_session()
        METRICS.add_clarify_questions(len(questions))
        _STORE.create(req.session_id, {
            "intent": intent,
            "gaps": gaps,
            "round": 1,
            "max_rounds": 2,
        })
        log_info("clarify", "questions", session_id=req.session_id, trace_id=trace_id, extra={"count": len(questions)})
        return ApiResponse(success=False, mode="clarify", questions=questions, round=1, max_rounds=2)
    # no gaps → run downstream
    try:
        result = continue_workflow(intent, req.session_id)
        log_info("workflow", "completed", session_id=req.session_id, trace_id=trace_id, extra={"latency_ms": int((time.time()-start_ts)*1000)})
        cache_put(intent, result)
        return ApiResponse(success=True, data=result)
    except DomainError as de:
        log_error("workflow", de.message, session_id=req.session_id, code=de.code, trace_id=trace_id)
        return ApiResponse(success=False, error=ErrorInfo(code=de.code, message=de.message, detail=de.detail))

@app.post("/api/mvp/plan_v2", response_model=ApiResponse)
async def post_plan_v2(req: PlanRequest, _: bool = Depends(require_auth)):
    """Parallel variant using orchestrate_parallel (flights+hotels)."""
    trace_id = new_trace_id()
    start_ts = time.time()
    log_info("api", "plan_v2_request", session_id=req.session_id, trace_id=trace_id)
    METRICS.inc_plan()
    if not rate_limit_allow(req.session_id):
        log_error("rate_limit", "exceeded", session_id=req.session_id, code="RATE_LIMIT_EXCEEDED", trace_id=trace_id)
        return ApiResponse(success=False, error=ErrorInfo(code="RATE_LIMIT_EXCEEDED", message="Too many requests"))
    try:
        intent = intent_parse(req.text, req.session_id)
        log_info("api", "intent_parsed", session_id=req.session_id, trace_id=trace_id, extra={
            "destination": intent.destination,
            "days": intent.days,
            "budget_total": intent.budget_total,
            "depart_date": str(intent.depart_date) if intent.depart_date else None,
        })
    except DomainError as de:
        log_error("intent_parse", de.message, session_id=req.session_id, code=de.code, trace_id=trace_id)
        return ApiResponse(success=False, error=ErrorInfo(code=de.code, message=de.message))
    gaps = intent_find_gaps(intent)
    if gaps:
        questions = intent_generate_questions(gaps)
        METRICS.inc_clarify_session()
        METRICS.add_clarify_questions(len(questions))
        _STORE.create(req.session_id, {"intent": intent, "gaps": gaps, "round": 1, "max_rounds": 2})
        log_info("clarify", "questions", session_id=req.session_id, trace_id=trace_id, extra={"count": len(questions), "variant": "v2"})
        return ApiResponse(success=False, mode="clarify", questions=questions, round=1, max_rounds=2)
    try:
        result = await orchestrate_parallel(intent, req.session_id)
        log_info("workflow", "completed_v2", session_id=req.session_id, trace_id=trace_id, extra={"latency_ms": int((time.time()-start_ts)*1000)})
        cache_put(intent, result)
        return ApiResponse(success=True, data=result)
    except DomainError as de:
        log_error("workflow", de.message, session_id=req.session_id, code=de.code, trace_id=trace_id)
        return ApiResponse(success=False, error=ErrorInfo(code=de.code, message=de.message, detail=de.detail))

@app.post("/api/mvp/plan/clarify", response_model=ApiResponse)
def post_clarify(req: ClarifyRequest, _: bool = Depends(require_auth)):
    trace_id = new_trace_id()
    start_ts = time.time()
    sess = _STORE.get(req.session_id)
    if not sess:
        log_error("clarify", "session_missing", session_id=req.session_id, code="SESSION_NOT_FOUND", trace_id=trace_id)
        return ApiResponse(success=False, error=ErrorInfo(code="SESSION_NOT_FOUND", message="Session missing"))
    intent: TripIntent = sess["intent"]
    # apply answers
    answer_dicts = [{"field": a.field, "value": a.value} for a in req.answers]
    intent_apply_answers(intent, answer_dicts)
    gaps = intent_find_gaps(intent)
    if gaps and sess["round"] < sess["max_rounds"]:
        sess["round"] += 1
        sess["gaps"] = gaps
        _STORE.update(req.session_id, **sess)
        questions = intent_generate_questions(gaps)
        METRICS.inc_clarify_round()
        METRICS.add_clarify_questions(len(questions))
        log_info("clarify", "questions_round", session_id=req.session_id, trace_id=trace_id, extra={"round": sess["round"], "count": len(questions)})
        return ApiResponse(success=False, mode="clarify", questions=questions, round=sess["round"], max_rounds=sess["max_rounds"])
    if "destination" in gaps:
        log_error("clarify", "destination_missing", session_id=req.session_id, code="INTENT_DESTINATION_MISSING", trace_id=trace_id)
        return ApiResponse(success=False, error=ErrorInfo(code="INTENT_DESTINATION_MISSING", message="Destination missing"))
    # finalize
    try:
        result = continue_workflow(intent, req.session_id)
        log_info("workflow", "completed", session_id=req.session_id, trace_id=trace_id, extra={"latency_ms": int((time.time()-start_ts)*1000)})
        _STORE.remove(req.session_id)
        cache_put(intent, result)
        return ApiResponse(success=True, data=result)
    except DomainError as de:
        log_error("workflow", de.message, session_id=req.session_id, code=de.code, trace_id=trace_id)
        return ApiResponse(success=False, error=ErrorInfo(code=de.code, message=de.message, detail=de.detail))

@app.get("/api/mvp/plan/{session_id}", response_model=ApiResponse)
def get_plan(session_id: str):
    sess = _STORE.get(session_id)
    if not sess:
        return ApiResponse(success=False, error=ErrorInfo(code="SESSION_NOT_FOUND", message="Session missing"))
    return ApiResponse(success=False, mode="clarify", questions=intent_generate_questions(sess["gaps"]), round=sess["round"], max_rounds=sess["max_rounds"])

@app.get("/api/mvp/health")
@app.get("/health")
def health():
    from datetime import datetime
    return {"status": "healthy", "service": "Travel Agent MVP", "time": datetime.utcnow().isoformat()}

@app.get("/api/mvp/metrics")
@app.get("/metrics")
def metrics():
    base = METRICS.snapshot()
    from .metrics import METRICS_PARALLEL, METRICS_GRAPH
    base.update({"parallel_runs": METRICS_PARALLEL.snapshot()["parallel_runs"], "graph_runs": METRICS_GRAPH.snapshot()["graph_runs"]})
    return base

@app.get("/api/mvp/prom_metrics")
@app.get("/metrics_prom")
def prom_metrics():
    data, ctype = export_prometheus()
    return Response(content=data, media_type=ctype)

@app.get("/api/mvp/errors")
@app.get("/errors_recent")
def recent_errors(limit: int = 50, since_seconds: int | None = None):
    return {"errors": ERROR_TRACKER.snapshot(limit=limit, since_seconds=since_seconds)}

@app.get("/api/mvp/llm_audit")
@app.get("/llm_audit_recent")
def llm_audit(limit: int = 50, since_seconds: int | None = None):
    data = PROMPT_AUDIT.snapshot(limit=limit, since_seconds=since_seconds)
    # backward compatibility: both keys
    return {"audit": data, "records": data}

@app.get("/routes")
def list_routes():
    routes = []
    for r in app.router.routes:
        if hasattr(r, 'path'):
            methods = list(getattr(r, 'methods', []))
            routes.append({"path": r.path, "methods": methods})
    return {"routes": routes, "count": len(routes)}

@app.post("/api/mvp/auth/token")
def issue_token(form: OAuth2PasswordRequestForm = Depends()):
    if not cfg.JWT_ENABLE:
        raise HTTPException(status_code=400, detail="JWT disabled")
    if form.username != cfg.AUTH_DEMO_USER or form.password != cfg.AUTH_DEMO_PASSWORD:
        raise HTTPException(status_code=401, detail="Bad credentials")
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=cfg.AUTH_JWT_EXPIRE_MIN)
    payload = {"sub": form.username, "exp": expire}
    token = jwt.encode(payload, cfg.AUTH_JWT_SECRET, algorithm=cfg.AUTH_JWT_ALG)
    return {"access_token": token, "token_type": "bearer", "expires_in_minutes": cfg.AUTH_JWT_EXPIRE_MIN}

@app.post("/api/mvp/debug/intent")
def debug_intent(req: DebugIntentRequest, _: bool = Depends(require_auth)):
    """Parse raw text and return intent object plus detected gaps.
    For debugging clarification behavior (origin now required).
    """
    intent = intent_parse(req.text, req.session_id)
    gaps = intent_find_gaps(intent)
    return {"intent": intent.model_dump(), "gaps": gaps}

@app.post("/api/mvp/plan_v3", response_model=ApiResponse)
def post_plan_v3(req: PlanRequest, _: bool = Depends(require_auth)):
    """LangGraph graph orchestration variant. Falls back to parallel if graph unavailable."""
    trace_id = new_trace_id()
    start_ts = time.time()
    log_info("api", "plan_v3_request", session_id=req.session_id, trace_id=trace_id)
    METRICS.inc_plan()
    if not rate_limit_allow(req.session_id):
        log_error("rate_limit", "exceeded", session_id=req.session_id, code="RATE_LIMIT_EXCEEDED", trace_id=trace_id)
        return ApiResponse(success=False, error=ErrorInfo(code="RATE_LIMIT_EXCEEDED", message="Too many requests"))
    try:
        intent = intent_parse(req.text, req.session_id)
    except DomainError as de:
        log_error("intent_parse", de.message, session_id=req.session_id, code=de.code, trace_id=trace_id)
        return ApiResponse(success=False, error=ErrorInfo(code=de.code, message=de.message))
    gaps = intent_find_gaps(intent)
    if gaps:
        questions = intent_generate_questions(gaps)
        METRICS.inc_clarify_session()
        METRICS.add_clarify_questions(len(questions))
        _STORE.create(req.session_id, {"intent": intent, "gaps": gaps, "round": 1, "max_rounds": 2})
        return ApiResponse(success=False, mode="clarify", questions=questions, round=1, max_rounds=2)
    try:
        from .metrics import METRICS_GRAPH
        result = run_graph(intent)
        METRICS_GRAPH.inc()
        log_info("workflow", "completed_v3_graph", session_id=req.session_id, trace_id=trace_id, extra={"latency_ms": int((time.time()-start_ts)*1000)})
    except Exception:
        # fallback to parallel orchestrator
        log_error("workflow", "graph_unavailable_fallback", session_id=req.session_id, code="GRAPH_FALLBACK", trace_id=trace_id)
        result = continue_workflow(intent, req.session_id)
    cache_put(intent, result)
    return ApiResponse(success=True, data=result)
