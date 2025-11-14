import pytest
from travel_agent.llm_manager import llm_safe_json, llm_select_model
from travel_agent.errors import DomainError


def test_llm_json_invalid():
    with pytest.raises(DomainError) as e:
        llm_safe_json("FAIL_JSON")
    assert e.value.code == "LLM_JSON_INVALID"


def test_llm_fallback_exhausted():
    # Force exhaustion by calling select beyond length
    from travel_agent.config import LLM_FALLBACKS
    with pytest.raises(DomainError) as e:
        llm_select_model(len(LLM_FALLBACKS) + 5)
    assert e.value.code == "LLM_FALLBACK_EXHAUSTED"