"""Itinerary generation wrapper.
Ref: §3.5 行程生成
"""
from __future__ import annotations
from typing import List
from .models import TripIntent, Itinerary, DayPlan
from .errors import DomainError
from .llm_manager import llm_itinerary_generate


def itinerary_generate(intent: TripIntent, spots: List[str]) -> Itinerary:
    if not intent.destination or not intent.days:
        raise DomainError("ITINERARY_GEN_FAIL", "Missing destination/days")
    return llm_itinerary_generate(intent, spots)
