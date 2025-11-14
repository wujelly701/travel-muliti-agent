from travel_agent.intent import intent_parse

def test_parse_basic():
    txt = "12月去东京5天 预算20000"
    intent = intent_parse(txt, "s1")
    assert intent.destination == "东京"
    assert intent.days == 5
    assert intent.depart_date is not None

def test_parse_missing_destination():
    txt = "预算2000 3天"  # no destination keyword
    intent = intent_parse(txt, "s2")
    assert intent.destination is None
