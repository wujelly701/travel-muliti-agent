from travel_agent.workflow import workflow_run

def test_workflow_run_end_to_end():
    result = workflow_run("sess1", "12月去东京5天 预算20000")
    assert result.intent.destination == "Tokyo" or result.intent.destination == "东京"
    assert result.itinerary.days
    assert result.budget.total > 0
    assert result.schema_version == "1.0"
