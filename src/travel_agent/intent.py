"""Intent parsing and clarification loop.
Ref: §3.1 意图解析 & §3.1A Clarification Loop
"""
from __future__ import annotations
import re
from datetime import date
from typing import List, Callable
from .models import TripIntent
from .errors import DomainError
from .config import CLARIFY_MAX_ROUNDS, INTENT_DEFAULT_ORIGIN

DESTINATION_REGEX = r"(?:(?:去|到)([\u4e00-\u9fa5A-Za-z]+))"
ORIGIN_REGEX = r"(?:从|出发自)([\u4e00-\u9fa5A-Za-z]+)"
DAYS_REGEX = r"(\d+)\s*天"
BUDGET_REGEX = r"预算\s*(\d+(?:\.\d+)?)"
DATE_REGEX = r"(20\d{2}-\d{1,2}-\d{1,2})"
MONTH_REGEX = r"(\d{1,2})月"  # fallback month only

REQUIRED_FIELDS = ["origin", "destination", "depart_date", "days"]


def intent_parse(raw_text: str, session_id: str, default_currency: str = 'CNY') -> TripIntent:
    """Parse minimal fields from raw text.
    Ref: §3.1
    """
    intent = TripIntent(session_id=session_id, raw_text=raw_text, currency=default_currency)

    # origin
    m_origin = re.search(ORIGIN_REGEX, raw_text)
    if m_origin:
        intent.origin = m_origin.group(1)

    # destination
    m_dest = re.search(DESTINATION_REGEX, raw_text)
    if m_dest:
        intent.destination = m_dest.group(1)

    # days
    m_days = re.search(DAYS_REGEX, raw_text)
    if m_days:
        intent.days = int(m_days.group(1))

    # budget
    m_budget = re.search(BUDGET_REGEX, raw_text)
    if m_budget:
        intent.budget_total = float(m_budget.group(1))

    # date exact
    m_date = re.search(DATE_REGEX, raw_text)
    if m_date:
        try:
            intent.depart_date = date.fromisoformat(m_date.group(1))
        except ValueError:
            pass
    else:
        # month only fallback (assume first day of month)
        m_month = re.search(MONTH_REGEX, raw_text)
        if m_month:
            # naive year assumption: current year
            from datetime import datetime
            year = datetime.utcnow().year
            month = int(m_month.group(1))
            intent.depart_date = date(year, month, 1)

    # finalize derived dates/nights
    intent.finalize_dates()

    return intent


def intent_find_gaps(intent: TripIntent) -> List[str]:
    gaps = []
    if not intent.origin:
        gaps.append("origin")
    if not intent.destination:
        gaps.append("destination")
    if not intent.depart_date:
        gaps.append("depart_date")
    if not intent.days:
        gaps.append("days")
    if intent.budget_total is None:
        gaps.append("budget_total")
    return gaps


def intent_generate_questions(gap_fields: List[str], locale: str = 'zh') -> List[dict]:
    mapping = {
        "origin": "您的出发城市是？",
        "destination": "请问您想去的城市或国家是？",
        "depart_date": "预计具体出发日期（例如 2025-12-10）是哪一天？",
        "days": "大概旅行几天？",
        "budget_total": "您的总预算（货币：CNY）是多少？若不确定可输入 '不确定'",
    }
    return [
        {"id": f"q_{f}", "field": f, "prompt": mapping[f], "required": True}
        for f in gap_fields
    ]


def intent_apply_answers(intent: TripIntent, answers: List[dict]) -> TripIntent:
    for a in answers:
        field = a.get("field")
        value = a.get("value")
        if field == "origin" and value:
            intent.origin = value.strip()
        elif field == "destination" and value:
            intent.destination = value.strip()
        elif field == "depart_date" and value:
            try:
                intent.depart_date = date.fromisoformat(value.strip())
            except ValueError:
                pass
        elif field == "days" and value:
            try:
                intent.days = int(value)
            except ValueError:
                pass
        elif field == "budget_total" and value and value != "不确定":
            try:
                intent.budget_total = float(value)
            except ValueError:
                pass
    intent.finalize_dates()
    return intent


def intent_clarify_loop(raw_text: str, session_id: str, user_answer_provider: Callable[[dict], str]) -> TripIntent:
    """Clarification loop up to CLARIFY_MAX_ROUNDS.
    Ref: §3.1A
    """
    intent = intent_parse(raw_text, session_id)
    round_idx = 0
    gaps = intent_find_gaps(intent)
    while gaps and round_idx < CLARIFY_MAX_ROUNDS:
        questions = intent_generate_questions(gaps)
        answers: List[dict] = []
        for q in questions:
            ans_raw = user_answer_provider(q)
            answers.append({"question_id": q["id"], "field": q["field"], "value": ans_raw})
        intent = intent_apply_answers(intent, answers)
        gaps = intent_find_gaps(intent)
        round_idx += 1
    if "destination" in gaps:
        raise DomainError("INTENT_DESTINATION_MISSING", "Destination still missing after clarification")
    return intent
