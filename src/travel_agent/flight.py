"""Flight search mock implementation.
Ref: §3.2 航班搜索
"""
from __future__ import annotations
from typing import List
from datetime import datetime, timedelta
from .models import TripIntent, FlightOption
from .errors import DomainError

DEFAULT_ORIGIN = "Shanghai"


def flight_score(price: float, duration_minutes: int, stops: int) -> float:
    # Normalize simplistic
    p_norm = 1 / (price + 1)
    d_norm = 1 / (duration_minutes + 1)
    s_norm = 1 / (stops + 1)
    return 0.5 * p_norm + 0.3 * d_norm + 0.2 * s_norm


def flight_search(intent: TripIntent, max_results: int = 5) -> List[FlightOption]:
    if not intent.destination or not intent.depart_date:
        raise DomainError("FLIGHT_API_FAIL", "Missing destination or depart_date")
    origin = intent.origin or DEFAULT_ORIGIN
    # mock flights
    base_time = datetime.combine(intent.depart_date, datetime.min.time())
    flights: List[FlightOption] = []
    for i in range(max_results):
        depart = base_time + timedelta(hours=8 + i)
        arrive = depart + timedelta(hours=2 + i)
        price = 3000 + i * 200
        duration = int((arrive - depart).total_seconds() / 60)
        stops = 0 if i < 2 else 1
        flights.append(FlightOption(
            id=f"FL{i}", airline="MockAir", flight_number=f"MA{i:03}",
            depart_airport=origin, arrive_airport=intent.destination, depart_time=depart,
            arrive_time=arrive, duration_minutes=duration, price=price, currency=intent.currency,
            cabin_class="Economy", stops=stops, score=flight_score(price, duration, stops)
        ))
    return flights
