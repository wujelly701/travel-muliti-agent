"""Real LLM adapter (OpenAI-compatible / DeepSeek-compatible).
Ref: §3.0 LLM选择与容错策略
Falls back to mock if API key missing or request fails.
"""
from __future__ import annotations
import httpx, json
from typing import List, Dict
from .config import (
    LLM_BASE_URL, OPENAI_API_KEY, DEEPSEEK_API_KEY, LLM_REQUEST_TIMEOUT,
    LLM_PRIMARY, LLM_FALLBACKS, LLM_ENABLE_HIGH_COST
)
from .errors import DomainError
from .logger import log_info, log_error


def _auth_key(model: str) -> str | None:
    # choose key by model prefix heuristic
    if model.startswith("deepseek"):
        return DEEPSEEK_API_KEY or OPENAI_API_KEY  # allow fallback
    return OPENAI_API_KEY or DEEPSEEK_API_KEY


def call_chat_completion(model: str, messages: List[Dict[str, str]], *, temperature: float = 0.3) -> str:
    key = _auth_key(model)
    if not key:
        raise DomainError("LLM_AUTH_MISSING", "No API key available")
    url = f"{LLM_BASE_URL}/chat/completions" if not LLM_BASE_URL.endswith("/chat/completions") else LLM_BASE_URL
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    try:
        with httpx.Client(timeout=LLM_REQUEST_TIMEOUT) as client:
            resp = client.post(url, json=payload, headers=headers)
        if resp.status_code >= 400:
            raise DomainError("LLM_HTTP_ERROR", f"{resp.status_code} {resp.text[:120]}")
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return content
    except DomainError:
        raise
    except Exception as e:
        raise DomainError("LLM_NETWORK_FAIL", str(e))


def ensure_json(content: str) -> Dict:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        raise DomainError("LLM_JSON_INVALID", "Invalid JSON from provider")


def chat_json(model: str, prompt: str) -> Dict:
    messages = [{"role": "user", "content": prompt}]
    content = call_chat_completion(model, messages)
    return ensure_json(content)
