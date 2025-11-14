"""Budget allocation.
Ref: §3.6 预算分配
"""
from __future__ import annotations
from typing import List
from .models import TripIntent, FlightOption, HotelOption, BudgetAllocation
from .errors import DomainError

DEFAULT_RATIO = {
    "transportation": 0.3,
    "accommodation": 0.25,
    "food": 0.2,
    "attractions": 0.15,
    "other": 0.10,
}

# Realism thresholds (heuristic)
DAILY_LOW_THRESHOLD = 150.0  # <150 CNY/day usually unrealistic for flights+lodging
DAILY_HIGH_THRESHOLD = 8000.0  # >8000 CNY/day likely excessive for typical leisure travel

def _derive_days(intent: TripIntent, hotels: List[HotelOption]) -> int | None:
    if intent.days:
        return intent.days
    # fallback: infer from first hotel nights + 1 (arrival + nights)
    if hotels:
        return hotels[0].nights + 1
    return None


def budget_allocate(intent: TripIntent, flights: List[FlightOption], hotels: List[HotelOption]) -> BudgetAllocation:
    if not flights or not hotels:
        raise DomainError("BUDGET_ALLOC_FAIL", "Missing flights/hotels")
    # estimate total if missing
    if intent.budget_total is None:
        # naive estimate: cheapest flight + hotel total * travelers * 1.4 buffer
        min_flight = min(f.price for f in flights)
        min_hotel = min(h.total_price for h in hotels)
        est = (min_flight + min_hotel) * intent.travelers * 1.4
        intent.budget_total = round(est, 2)
        warnings = ["BUDGET_ESTIMATED"]
    else:
        warnings = []
    total = intent.budget_total
    alloc = {k: round(total * v, 2) for k, v in DEFAULT_RATIO.items()}
    # sanity check transportation realism
    if alloc["transportation"] < min(f.price for f in flights):
        warnings.append("TRANSPORT_BUDGET_LOW")
    # daily realism checks
    days = _derive_days(intent, hotels)
    if days and days > 0:
        daily = total / days
        if daily < DAILY_LOW_THRESHOLD:
            warnings.append("DAILY_BUDGET_TOO_LOW")
        elif daily > DAILY_HIGH_THRESHOLD:
            warnings.append("DAILY_BUDGET_TOO_HIGH")
    return BudgetAllocation(total=total, currency=intent.currency, warnings=warnings, **alloc)
