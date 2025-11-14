from travel_agent.intent import intent_parse, intent_find_gaps


def test_origin_missing_triggers_gap():
    raw = '预算3000 去上海 3天 2025-12-10'
    intent = intent_parse(raw, session_id='o1')
    gaps = intent_find_gaps(intent)
    assert 'origin' in gaps
    assert 'destination' not in gaps


def test_origin_present_removes_gap():
    raw = '预算3000 从北京去上海 3天 2025-12-10'
    intent = intent_parse(raw, session_id='o2')
    gaps = intent_find_gaps(intent)
    assert 'origin' not in gaps
    assert 'destination' not in gaps
