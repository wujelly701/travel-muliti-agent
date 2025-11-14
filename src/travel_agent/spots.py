"""Basic spot fetch.
Ref: §3.4 景点基础推荐
"""
from typing import List, Optional
from .errors import DomainError

DEFAULT_SPOTS = ["博物馆", "中央公园", "美食街", "历史广场", "河畔步道"]


def spot_fetch_basic(destination: str, categories: Optional[List[str]] = None, limit: int = 10) -> List[str]:
    if not destination:
        raise DomainError("SPOT_FETCH_FAIL", "Destination missing")
    spots = DEFAULT_SPOTS.copy()
    if categories:
        # naive category influence: append category labels
        for c in categories:
            spots.append(f"{c}推荐地")
    return spots[:limit]
