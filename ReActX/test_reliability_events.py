"""
Minimal test for add_reliability_event helper.
No real LLM, no Docker, no run_closed_loop.
"""
from app.loop.closed_loop_runner import add_reliability_event

events = []

add_reliability_event(
    events, "memory", "memory_retrieved",
    status="info",
    details={"count": 2},
)
add_reliability_event(
    events, "eval", "eval_completed",
    status="fail",
    details={"step": 1, "success": False, "score": 0.8},
)
add_reliability_event(
    events, "loop", "retry_triggered",
    details={"step": 1},
)

assert len(events) == 3, f"expected 3 events, got {len(events)}"

for e in events:
    assert "stage" in e, f"missing 'stage' in {e}"
    assert "event" in e, f"missing 'event' in {e}"
    assert "status" in e, f"missing 'status' in {e}"
    assert "details" in e, f"missing 'details' in {e}"

assert events[0]["event"] == "memory_retrieved"
assert events[1]["event"] == "eval_completed"
assert events[2]["event"] == "retry_triggered"

print("[TEST PASS] reliability events logged correctly")
