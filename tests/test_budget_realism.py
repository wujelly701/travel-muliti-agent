from datetime import date
from travel_agent.models import TripIntent
from travel_agent.flight import flight_search
from travel_agent.hotel import hotel_search
from travel_agent.budget import budget_allocate


def _base_intent(budget: float, days: int) -> TripIntent:
    return TripIntent(
        session_id="S1",
        raw_text="Test",
        destination="Beijing",
        origin="Shanghai",
        depart_date=date(2025, 1, 10),
        days=days,
        budget_total=budget,
        travelers=1,
    )


def test_budget_realism_low_daily():
    intent = _base_intent(budget=400.0, days=5)  # 80/day < threshold
    flights = flight_search(intent, max_results=1)
    hotels = hotel_search(intent, max_results=1)
    alloc = budget_allocate(intent, flights, hotels)
    assert "DAILY_BUDGET_TOO_LOW" in alloc.warnings
    assert any(w in alloc.warnings for w in ["TRANSPORT_BUDGET_LOW", "DAILY_BUDGET_TOO_LOW"])  # sanity


def test_budget_realism_high_daily():
    intent = _base_intent(budget=60000.0, days=3)  # 20000/day > high threshold
    flights = flight_search(intent, max_results=1)
    hotels = hotel_search(intent, max_results=1)
    alloc = budget_allocate(intent, flights, hotels)
    assert "DAILY_BUDGET_TOO_HIGH" in alloc.warnings
