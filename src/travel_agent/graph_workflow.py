"""LangGraph-based multi-agent orchestration.
If LangGraph import fails, provide fallback stub.
"""
from __future__ import annotations
from typing import Any, Dict
from .models import TripIntent, PlanningResult
from .flight import flight_search
from .hotel import hotel_search
from .spots import spot_fetch_basic
from .itinerary import itinerary_generate
from .budget import budget_allocate
from datetime import datetime
from .metrics import METRICS_PARALLEL
from .logger import log_info

try:
    from langgraph.graph import Graph
except Exception:  # pragma: no cover
    Graph = None  # type: ignore


def build_graph():
    if Graph is None:
        return None
    g = Graph()

    def node_flights(state: Dict[str, Any]):
        intent: TripIntent = state['intent']
        flights = flight_search(intent)
        log_info('graph', 'flights_done', session_id=intent.session_id, extra={'count': len(flights)})
        state['flights'] = flights
        return state

    def node_hotels(state: Dict[str, Any]):
        intent: TripIntent = state['intent']
        hotels = hotel_search(intent)
        log_info('graph', 'hotels_done', session_id=intent.session_id, extra={'count': len(hotels)})
        state['hotels'] = hotels
        return state

    def node_spots(state: Dict[str, Any]):
        intent: TripIntent = state['intent']
        spots = spot_fetch_basic(intent.destination, intent.preferences)
        log_info('graph', 'spots_done', session_id=intent.session_id, extra={'count': len(spots)})
        state['spots'] = spots
        return state

    def node_itinerary(state: Dict[str, Any]):
        intent: TripIntent = state['intent']
        itinerary = itinerary_generate(intent, state.get('spots', []))
        log_info('graph', 'itinerary_done', session_id=intent.session_id)
        state['itinerary'] = itinerary
        return state

    def node_budget(state: Dict[str, Any]):
        intent: TripIntent = state['intent']
        budget = budget_allocate(intent, state.get('flights', []), state.get('hotels', []))
        log_info('graph', 'budget_done', session_id=intent.session_id)
        state['budget'] = budget
        return state

    g.add_node('flights', node_flights)
    g.add_node('hotels', node_hotels)
    g.add_node('spots', node_spots)
    g.add_node('itinerary', node_itinerary)
    g.add_node('budget', node_budget)

    # edges: start -> flights/hotels; both -> spots -> itinerary -> budget
    g.set_entry_point('flights')
    g.add_edge('flights', 'spots')
    g.add_edge('hotels', 'spots')
    g.add_edge('spots', 'itinerary')
    g.add_edge('itinerary', 'budget')

    g.set_finish_point('budget')
    return g

_GRAPH = build_graph()


def run_graph(intent: TripIntent) -> PlanningResult:
    if _GRAPH is None:
        raise RuntimeError('LangGraph not available')
    state = {'intent': intent}
    result_state = _GRAPH.run(state)  # synchronous run
    flights = result_state['flights']
    hotels = result_state['hotels']
    itinerary = result_state['itinerary']
    budget = result_state['budget']
    return PlanningResult(
        session_id=intent.session_id,
        intent=intent,
        flights=flights,
        hotels=hotels,
        itinerary=itinerary,
        budget=budget,
        generated_at=datetime.utcnow(),
        warnings=[]
    )
