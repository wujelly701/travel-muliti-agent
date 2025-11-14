"""Hotel search mock implementation.
Ref: §3.3 酒店搜索
"""
from __future__ import annotations
from typing import List, Optional
from .models import TripIntent, HotelOption
from .errors import DomainError


def hotel_score(price_per_night: float, rating: float) -> float:
    p_norm = 1 / (price_per_night + 1)
    r_norm = rating / 5.0
    return 0.6 * r_norm + 0.4 * p_norm


def hotel_search(intent: TripIntent, nights: Optional[int] = None, max_results: int = 5) -> List[HotelOption]:
    if not intent.destination or not intent.days:
        raise DomainError("HOTEL_API_FAIL", "Missing destination or days")
    nights = nights or (intent.nights or (intent.days - 1))
    hotels: List[HotelOption] = []
    for i in range(max_results):
        price = 400 + i * 50
        rating = 4.0 - (i * 0.1)
        total = price * nights
        hotels.append(HotelOption(
            id=f"HT{i}", name=f"Hotel{i}", location_text=f"Center {i}", price_per_night=price,
            nights=nights, total_price=total, currency=intent.currency, rating=rating,
            distance_center_km=0.5 + i * 0.3, score=hotel_score(price, rating)
        ))
    return hotels
