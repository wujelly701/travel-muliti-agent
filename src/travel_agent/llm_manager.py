"""LLM invocation & fallback mock implementation.
Ref: §3.0 LLM选择与容错策略
"""
from __future__ import annotations
from typing import List, Dict
import json
from .errors import DomainError
from .config import LLM_PRIMARY, LLM_FALLBACKS, LLM_MAX_REPAIR, LLM_ENABLE_HIGH_COST
from .llm_adapter import chat_json
from .logger import log_info, log_error
from .metrics import METRICS
from .prompt_audit import PROMPT_AUDIT

def llm_select_model(index: int = 0) -> str:
    """Select model by index through primary+fallback chain."""
    chain = [LLM_PRIMARY] + LLM_FALLBACKS
    if index < len(chain):
        return chain[index]
    raise DomainError("LLM_FALLBACK_EXHAUSTED", "All models exhausted")

def llm_invoke(model: str, prompt: str, *, json_mode: bool = True, timeout: int = 25) -> str:
    start = __import__("time").time()
    # Explicit failure trigger for test scenario
    if "FAIL_JSON" in prompt:
        return "NOT VALID JSON"
    METRICS.llm_call()
    try:
        # real call attempt
        if json_mode:
            # expect provider returns JSON directly
            data = chat_json(model, prompt)
            raw = json.dumps(data, ensure_ascii=False)
        else:
            data = chat_json(model, prompt)
            raw = json.dumps(data, ensure_ascii=False)
        log_info("llm", "success", extra={"model": model, "json_mode": json_mode}, session_id="n/a", start_ts=start)
        return raw
    except DomainError as de:
        METRICS.llm_error()
        log_error("llm", de.message, code=de.code, session_id="n/a", extra={"model": model})
        # fallback to mock content
        if "GENERATE_ITINERARY" in prompt:
            METRICS.llm_fallback()
            return json.dumps({
                "days": [{"day_index": 1, "main_spots": ["自由活动"], "meals": ["早餐","午餐","晚餐"], "notes": "占位(降级)"}],
                "summary": "占位行程 (LLM降级)"
            }, ensure_ascii=False)
        return json.dumps({"parsed": True, "fallback": True}, ensure_ascii=False)

def llm_safe_json(prompt: str) -> Dict:
    """Attempt JSON parse with single repair cycle.
    Ref: §3.0 容错机制
    """
    last_raw = ""
    last_model = ""
    for attempt in range(LLM_MAX_REPAIR + 1):
        model = llm_select_model(attempt)
        last_model = model
        raw = llm_invoke(model, prompt, json_mode=True)
        last_raw = raw
        try:
            parsed = json.loads(raw)
            PROMPT_AUDIT.record(model=model, prompt_tag="itinerary" if "GENERATE_ITINERARY" in prompt else "generic", prompt=prompt,
                                response=raw, json_valid=True, repair_attempts=attempt, fallback_used=(attempt > 0), error_code=None)
            return parsed
        except json.JSONDecodeError:
            if attempt >= LLM_MAX_REPAIR:
                PROMPT_AUDIT.record(model=model, prompt_tag="itinerary" if "GENERATE_ITINERARY" in prompt else "generic", prompt=prompt,
                                    response=raw, json_valid=False, repair_attempts=attempt, fallback_used=True, error_code="LLM_JSON_INVALID")
                raise DomainError("LLM_JSON_INVALID", "JSON repair failed")
            METRICS.llm_fallback()
            prompt += "\n请只输出有效 JSON"  # modify prompt and retry
    PROMPT_AUDIT.record(model=last_model, prompt_tag="itinerary" if "GENERATE_ITINERARY" in prompt else "generic", prompt=prompt,
                        response=last_raw, json_valid=False, repair_attempts=LLM_MAX_REPAIR, fallback_used=True, error_code="LLM_JSON_INVALID")
    raise DomainError("LLM_JSON_INVALID", "Unexpected path")

def llm_itinerary_generate(intent, spots: List[str]):
    """Generate itinerary using mock LLM response.
    Ref: §3.5 行程生成 NOTE + §3.0 fallback
    """
    payload = llm_safe_json("GENERATE_ITINERARY")
    from .models import DayPlan, Itinerary
    day_plans = [DayPlan(day_index=d["day_index"], date=intent.depart_date, main_spots=d["main_spots"], meals=d["meals"], notes=d.get("notes")) for d in payload["days"]]
    return Itinerary(days=day_plans, summary=payload["summary"])
