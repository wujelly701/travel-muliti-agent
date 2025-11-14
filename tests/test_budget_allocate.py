from travel_agent.models import TripIntent
from travel_agent.flight import flight_search
from travel_agent.hotel import hotel_search
from travel_agent.budget import budget_allocate
from datetime import date


def test_budget_estimated_warning():
    intent = TripIntent(session_id="b1", raw_text="", destination="Tokyo", depart_date=date.today(), days=3)
    intent.finalize_dates()
    flights = flight_search(intent)
    hotels = hotel_search(intent)
    # Remove budget to trigger estimation
    intent.budget_total = None
    allocation = budget_allocate(intent, flights, hotels)
    assert "BUDGET_ESTIMATED" in allocation.warnings


def test_transport_budget_low_warning():
    intent = TripIntent(session_id="b2", raw_text="", destination="Tokyo", depart_date=date.today(), days=3, budget_total=1000)
    intent.finalize_dates()
    flights = flight_search(intent)
    hotels = hotel_search(intent)
    allocation = budget_allocate(intent, flights, hotels)
    assert "TRANSPORT_BUDGET_LOW" in allocation.warnings