"""Dump public function signatures for drift guard.
Run:
    PYTHONPATH=src python scripts/dump_signatures.py > signatures.json
"""
from __future__ import annotations
import inspect, json
import travel_agent.intent as intent
import travel_agent.flight as flight
import travel_agent.hotel as hotel
import travel_agent.spots as spots
import travel_agent.itinerary as itinerary
import travel_agent.budget as budget
import travel_agent.workflow as workflow

modules = [intent, flight, hotel, spots, itinerary, budget, workflow]
output = {}
for m in modules:
    funcs = {}
    for name, obj in inspect.getmembers(m, inspect.isfunction):
        if obj.__module__ == m.__name__ and not name.startswith("_"):
            sig = str(inspect.signature(obj))
            funcs[name] = sig
    output[m.__name__] = funcs

print(json.dumps(output, ensure_ascii=False, indent=2))