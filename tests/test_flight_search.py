from travel_agent.models import TripIntent
from travel_agent.flight import flight_search
import pytest
from datetime import date
from travel_agent.errors import DomainError

def test_flight_search_ok():
    intent = TripIntent(session_id="s", raw_text="", destination="Tokyo", depart_date=date.today(), days=3)
    intent.finalize_dates()
    flights = flight_search(intent)
    assert len(flights) >= 3
    assert all(f.score > 0 for f in flights)

def test_flight_search_missing():
    intent = TripIntent(session_id="s", raw_text="", destination=None, depart_date=None, days=None)
    with pytest.raises(DomainError):
        flight_search(intent)
