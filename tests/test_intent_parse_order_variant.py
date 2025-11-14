from travel_agent.intent import intent_parse, intent_find_gaps

def test_order_variant_all_fields_parsed():
    raw = '预算3000 去杭州 3天 2025-12-10'
    intent = intent_parse(raw, session_id='ord1')
    assert intent.destination == '杭州'
    assert intent.days == 3
    assert intent.budget_total == 3000.0
    assert str(intent.depart_date) == '2025-12-10'
    gaps = intent_find_gaps(intent)
    # budget_total not required gap but verify not missing
    assert 'destination' not in gaps
    assert 'days' not in gaps
    assert 'depart_date' not in gaps
