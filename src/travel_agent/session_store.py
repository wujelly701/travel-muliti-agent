"""Session store abstraction.
Ref: §7 会话与缓存策略

- InMemorySessionStore: original simple dict backend
- RedisSessionStore: optional, activated if redis library + REDIS_URL available
"""
from __future__ import annotations
from typing import Dict, Any, Optional, List
import json
from pydantic import BaseModel

try:  # optional dependency
    import redis  # type: ignore
except ImportError:  # pragma: no cover
    redis = None  # type: ignore

class InMemorySessionStore:
    def __init__(self):
        self._data: Dict[str, Dict[str, Any]] = {}

    def create(self, session_id: str, payload: Dict[str, Any]):
        self._data[session_id] = payload

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self._data.get(session_id)

    def update(self, session_id: str, **fields):
        if session_id in self._data:
            self._data[session_id].update(fields)

    def remove(self, session_id: str):
        self._data.pop(session_id, None)

    def keys(self) -> List[str]:
        return list(self._data.keys())

class RedisSessionStore:
    def __init__(self, url: str, prefix: str = "sess:"):
        if redis is None:  # pragma: no cover
            raise RuntimeError("redis library not installed")
        # decode_responses ensures str not bytes
        self.client = redis.Redis.from_url(url, decode_responses=True)
        self.prefix = prefix

    def _k(self, session_id: str) -> str:
        return f"{self.prefix}{session_id}"

    def _prepare(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for k, v in payload.items():
            if isinstance(v, BaseModel):
                # Fully JSON-serializable dict via model_dump_json
                out[k] = json.loads(v.model_dump_json())
            else:
                out[k] = v
        return out

    def create(self, session_id: str, payload: Dict[str, Any]):
        prepared = self._prepare(payload)
        self.client.set(self._k(session_id), json.dumps(prepared, ensure_ascii=False))

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        raw = self.client.get(self._k(session_id))
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:  # pragma: no cover
            return None

    def update(self, session_id: str, **fields):
        payload = self.get(session_id)
        if payload is None:
            return
        payload.update(fields)
        prepared = self._prepare(payload)
        self.client.set(self._k(session_id), json.dumps(prepared, ensure_ascii=False))

    def remove(self, session_id: str):
        self.client.delete(self._k(session_id))

    def keys(self) -> List[str]:  # pragma: no cover (depends on live redis)
        pattern = f"{self.prefix}*"
        return [k[len(self.prefix):] for k in self.client.scan_iter(pattern=pattern)]

def create_session_store(redis_url: str | None) -> InMemorySessionStore | RedisSessionStore:
    if redis_url and redis is not None:
        try:
            store = RedisSessionStore(redis_url)
            # test connectivity early; if fails fallback silently
            store.client.ping()
            return store
        except Exception:  # pragma: no cover
            return InMemorySessionStore()
    return InMemorySessionStore()

__all__ = [
    "InMemorySessionStore",
    "RedisSessionStore",
    "create_session_store",
]
