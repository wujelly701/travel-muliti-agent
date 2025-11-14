"""Core Pydantic models.
Ref: §2 数据模型与统一类型规范 + schema_version in PlanningResult
"""
from __future__ import annotations
from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import date, datetime, timedelta

class TripIntent(BaseModel):
    session_id: str
    raw_text: str
    language: Literal['zh','en'] = 'zh'
    origin: Optional[str] = None
    destination: Optional[str] = None
    depart_date: Optional[date] = None
    return_date: Optional[date] = None
    days: Optional[int] = None
    budget_total: Optional[float] = None
    travelers: int = 1
    preferences: List[str] = []
    currency: str = 'CNY'
    nights: Optional[int] = None  # Ref: §3.1A days/nights semantics

    def finalize_dates(self) -> None:
        if self.depart_date and self.days and not self.return_date:
            # default return_date = depart + (days - 1)
            self.return_date = self.depart_date + timedelta(days=self.days - 1)
        if self.depart_date and self.days and self.nights == self.days:
            # extra night case: return_date = depart + days
            self.return_date = self.depart_date + timedelta(days=self.days)
        if self.nights is None and self.days:
            self.nights = max(self.days - 1, 1)

class FlightOption(BaseModel):
    id: str
    airline: str
    flight_number: str
    depart_airport: str
    arrive_airport: str
    depart_time: datetime
    arrive_time: datetime
    duration_minutes: int
    price: float
    currency: str
    cabin_class: str
    stops: int
    source: Literal['mock'] = 'mock'
    score: float

class HotelOption(BaseModel):
    id: str
    name: str
    location_text: str
    price_per_night: float
    nights: int
    total_price: float
    currency: str
    rating: float
    source: Literal['mock'] = 'mock'
    distance_center_km: Optional[float] = None
    score: float

class DayPlan(BaseModel):
    day_index: int
    date: date
    main_spots: List[str]
    meals: List[str]
    notes: Optional[str] = None
    ugc_refs: Optional[List[str]] = None  # future placeholder (Ref: §8.5)

class Itinerary(BaseModel):
    days: List[DayPlan]
    summary: str

class BudgetAllocation(BaseModel):
    total: float
    currency: str
    transportation: float
    accommodation: float
    food: float
    attractions: float
    other: float
    warnings: List[str] = []

class PlanningResult(BaseModel):
    session_id: str
    schema_version: str = "1.0"
    intent: TripIntent
    flights: List[FlightOption]
    hotels: List[HotelOption]
    itinerary: Itinerary
    budget: BudgetAllocation
    generated_at: datetime
    warnings: List[str] = []
    realtime_supported: bool = False  # placeholder

class ErrorInfo(BaseModel):
    code: str
    message: str
    detail: Optional[str] = None

class ApiResponse(BaseModel):
    success: bool
    data: Optional[PlanningResult] = None
    error: Optional[ErrorInfo] = None
    mode: Optional[str] = None  # clarify when success=False & mode='clarify'
    questions: Optional[List[dict]] = None
    round: Optional[int] = None
    max_rounds: Optional[int] = None
