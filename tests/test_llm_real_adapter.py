import json
import pytest
from travel_agent.llm_manager import llm_safe_json
from travel_agent.llm_adapter import call_chat_completion
from travel_agent.errors import DomainError


class DummyResp:
    def __init__(self, status_code=200, content=None):
        self.status_code = status_code
        self._content = content or {
            "choices": [{"message": {"content": json.dumps({"days": [{"day_index": 1, "main_spots": ["景点A"], "meals": ["早餐","午餐","晚餐"], "notes": "ok"}], "summary": "测试"}, ensure_ascii=False)}}]
        }
        self.text = "ERR" if status_code >= 400 else json.dumps(self._content, ensure_ascii=False)

    def json(self):
        return self._content


def test_llm_adapter_success(monkeypatch):
    # monkeypatch httpx.Client.post
    import httpx
    def fake_post(self, url, json=None, headers=None):  # noqa: A002
        return DummyResp()
    monkeypatch.setattr(httpx.Client, "post", fake_post)
    # Provide prompt expecting itinerary json
    data = llm_safe_json("GENERATE_ITINERARY")
    assert "days" in data
    assert data["days"][0]["day_index"] == 1


def test_llm_adapter_http_error(monkeypatch):
    import httpx
    def fake_post(self, url, json=None, headers=None):  # noqa: A002
        return DummyResp(status_code=500)
    monkeypatch.setattr(httpx.Client, "post", fake_post)
    # Should fallback internally and still produce structure
    data = llm_safe_json("GENERATE_ITINERARY")
    assert "days" in data
    # summary indicates fallback
    assert "占位" in data.get("summary", "") or "行程" in data.get("summary", "")
