"""Workflow orchestration.
Ref: §3.8 工作流执行入口 + §4 工作流编排
"""
from __future__ import annotations
from typing import List, Tuple
import asyncio
from datetime import datetime
from .models import TripIntent, PlanningResult
from .intent import intent_clarify_loop, intent_parse
from .flight import flight_search
from .hotel import hotel_search
from .spots import spot_fetch_basic
from .itinerary import itinerary_generate
from .budget import budget_allocate
from .errors import DomainError
from .logger import log_info, log_error
from .metrics import METRICS


def continue_workflow(intent: TripIntent, session_id: str) -> PlanningResult:
    """Execute downstream steps assuming intent finalized.
    Ref: §3.8
    """
    start_ts = __import__("time").time()
    flights = flight_search(intent)
    log_info("flights", "retrieved", session_id=session_id, extra={"count": len(flights)})
    hotels = hotel_search(intent)
    log_info("hotels", "retrieved", session_id=session_id, extra={"count": len(hotels)})
    spots = spot_fetch_basic(intent.destination, intent.preferences)
    log_info("spots", "retrieved", session_id=session_id, extra={"count": len(spots)})
    itinerary = itinerary_generate(intent, spots)
    log_info("itinerary", "generated", session_id=session_id)
    budget = budget_allocate(intent, flights, hotels)
    log_info("budget", "allocated", session_id=session_id)
    latency_ms = (__import__("time").time() - start_ts) * 1000.0
    METRICS.record_workflow_latency(latency_ms)
    return PlanningResult(
        session_id=session_id,
        intent=intent,
        flights=flights,
        hotels=hotels,
        itinerary=itinerary,
        budget=budget,
        generated_at=datetime.utcnow(),
        warnings=[]
    )


async def _parallel_flights_hotels(intent: TripIntent) -> Tuple[List[dict], List[dict]]:
    loop = asyncio.get_running_loop()
    flights_task = loop.run_in_executor(None, flight_search, intent)
    hotels_task = loop.run_in_executor(None, hotel_search, intent)
    flights, hotels = await asyncio.gather(flights_task, hotels_task)
    return flights, hotels


async def orchestrate_parallel(intent: TripIntent, session_id: str) -> PlanningResult:
    """Parallel variant: flights + hotels concurrently then remaining sequential steps.
    Used by /plan_v2 endpoint.
    """
    start_ts = __import__('time').time()
    flights, hotels = await _parallel_flights_hotels(intent)
    log_info("flights", "retrieved", session_id=session_id, extra={"count": len(flights), "mode": "parallel"})
    log_info("hotels", "retrieved", session_id=session_id, extra={"count": len(hotels), "mode": "parallel"})
    spots = spot_fetch_basic(intent.destination, intent.preferences)
    log_info("spots", "retrieved", session_id=session_id, extra={"count": len(spots)})
    itinerary = itinerary_generate(intent, spots)
    log_info("itinerary", "generated", session_id=session_id)
    budget = budget_allocate(intent, flights, hotels)
    log_info("budget", "allocated", session_id=session_id)
    latency_ms = (__import__('time').time() - start_ts) * 1000.0
    METRICS.record_workflow_latency(latency_ms)
    # custom metric increment for parallel variant
    try:
        from .metrics import METRICS_PARALLEL  # may not exist yet
        METRICS_PARALLEL.inc_parallel()
    except Exception:
        pass
    return PlanningResult(
        session_id=session_id,
        intent=intent,
        flights=flights,
        hotels=hotels,
        itinerary=itinerary,
        budget=budget,
        generated_at=datetime.utcnow(),
        warnings=[]
    )


def workflow_run(session_id: str, raw_text: str, clarify: bool = True) -> PlanningResult:
    """Legacy helper kept for tests; performs auto clarification then downstream.
    Will be deprecated once external clarify flow used.
    """
    log_info("workflow", "start", session_id=session_id)
    if clarify:
        def provider(q: dict) -> str:
            field = q.get("field")
            if field == "destination":
                return "Tokyo"
            if field == "depart_date":
                from datetime import date
                return date.today().isoformat()
            if field == "days":
                return "3"
            if field == "budget_total":
                return "20000"
            return ""
        try:
            intent = intent_clarify_loop(raw_text, session_id, provider)
        except DomainError as de:
            log_error("clarify", de.message, session_id=session_id, code=de.code)
            raise
    else:
        intent = intent_parse(raw_text, session_id)
    log_info("intent", "finalized", session_id=session_id)
    return continue_workflow(intent, session_id)
