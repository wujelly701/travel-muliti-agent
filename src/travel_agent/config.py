"""Configuration loader.
Ref: §3.0 环境变量 + §3.1A Clarify settings
"""
from __future__ import annotations
import os
from typing import List

# Defaults per spec
_DEFAULT_PRIMARY = "deepseek-chat"
_DEFAULT_FALLBACKS = ["gpt-3.5-turbo", "gpt-4o", "claude-sonnet-4.5"]
_DEFAULT_CLARIFY_ROUNDS = 2
_DEFAULT_ORIGIN = "Shanghai"

LLM_PRIMARY: str = os.getenv("LLM_PRIMARY", _DEFAULT_PRIMARY)
LLM_FALLBACKS: List[str] = os.getenv("LLM_FALLBACKS", ",".join(_DEFAULT_FALLBACKS)).split(",")
CLARIFY_MAX_ROUNDS: int = int(os.getenv("CLARIFY_MAX_ROUNDS", str(_DEFAULT_CLARIFY_ROUNDS)))
INTENT_DEFAULT_ORIGIN: str = os.getenv("INTENT_DEFAULT_ORIGIN", _DEFAULT_ORIGIN)
LLM_MAX_REPAIR: int = int(os.getenv("LLM_MAX_REPAIR", "1"))
LLM_ENABLE_HIGH_COST: bool = os.getenv("LLM_ENABLE_HIGH_COST", "false").lower() == "true"

__all__ = [
    "LLM_PRIMARY",
    "LLM_FALLBACKS",
    "CLARIFY_MAX_ROUNDS",
    "INTENT_DEFAULT_ORIGIN",
    "LLM_MAX_REPAIR",
    "LLM_ENABLE_HIGH_COST",
]

# Real LLM adapter related env (optional)
LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
DEEPSEEK_API_KEY: str | None = os.getenv("DEEPSEEK_API_KEY")
LLM_REQUEST_TIMEOUT: int = int(os.getenv("LLM_REQUEST_TIMEOUT", "30"))
REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
RATE_LIMIT_REQUESTS_PER_MIN: int = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MIN", "10"))
RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
API_KEY: str | None = os.getenv("API_KEY")

__all__ += [
    "LLM_BASE_URL",
    "OPENAI_API_KEY",
    "DEEPSEEK_API_KEY",
    "LLM_REQUEST_TIMEOUT",
    "REDIS_URL",
    "RATE_LIMIT_REQUESTS_PER_MIN",
    "RATE_LIMIT_WINDOW_SECONDS",
    "API_KEY",
]
