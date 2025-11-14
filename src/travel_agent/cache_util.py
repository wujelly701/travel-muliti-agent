"""Intent canonical hash + result cache abstraction."""
from __future__ import annotations
import hashlib, json
from typing import Optional
from .models import TripIntent, PlanningResult
from .session_store import create_session_store
from .config import REDIS_URL

_CACHE_STORE = create_session_store(None)  # always in-memory for deterministic tests; Redis optional could be added later

def cache_clear():  # test helper
    try:
        if hasattr(_CACHE_STORE, '_data'):
            _CACHE_STORE._data = {}
    except Exception:
        pass

def intent_canonical(intent: TripIntent) -> dict:
    return {
        "destination": intent.destination,
        "depart_date": intent.depart_date.isoformat() if intent.depart_date else None,
        "days": intent.days,
        "origin": intent.origin,
        "travelers": intent.travelers,
        "preferences": sorted(intent.preferences),
        "currency": intent.currency,
    }

def intent_hash(intent: TripIntent) -> str:
    s = json.dumps(intent_canonical(intent), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:32]

def cache_get(intent: TripIntent) -> Optional[PlanningResult]:
    key = intent_hash(intent)
    stored = _CACHE_STORE.get(f"cache:{key}")
    if not stored:
        return None
    from .models import PlanningResult
    try:
        return PlanningResult(**stored["result"])
    except Exception:
        return None

def cache_put(intent: TripIntent, result: PlanningResult) -> None:
    key = intent_hash(intent)
    _CACHE_STORE.create(f"cache:{key}", {"result": json.loads(result.model_dump_json())})

__all__ = ["intent_hash", "cache_get", "cache_put", "cache_clear"]