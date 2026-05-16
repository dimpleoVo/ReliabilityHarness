"""
Minimal test for compute_retry_effectiveness.
No LLM, no Docker.
"""
from app.loop.retry_effectiveness import compute_retry_effectiveness

TRAJ_TWO = [
    {"step": 1, "traj": {}, "eval": {}},
    {"step": 2, "traj": {}, "eval": {}},
]

# ── Test 1: higher_is_better, 0.0 → 1.0 ──
result = compute_retry_effectiveness(
    trajectory_all=TRAJ_TWO,
    reliability_report={"score_before": 0.0, "score_after": 1.0},
    metric_direction="higher_is_better",
)

assert result["retry_triggered"] is True, f"retry_triggered: {result['retry_triggered']}"
assert result["attempts"] == 2, f"attempts: {result['attempts']}"
assert result["score_before"] == 0.0, f"score_before: {result['score_before']}"
assert result["score_after"] == 1.0, f"score_after: {result['score_after']}"
assert result["score_delta"] == 1.0, f"score_delta: {result['score_delta']}"
assert result["improved"] is True, f"improved: {result['improved']}"
assert result["recovered_from_failure"] is True, f"recovered_from_failure: {result['recovered_from_failure']}"

# ── Test 2: lower_is_better, 0.8 → 0.0 ──
result2 = compute_retry_effectiveness(
    trajectory_all=TRAJ_TWO,
    reliability_report={"score_before": 0.8, "score_after": 0.0},
    metric_direction="lower_is_better",
)

assert result2["retry_triggered"] is True, f"retry_triggered: {result2['retry_triggered']}"
assert result2["attempts"] == 2, f"attempts: {result2['attempts']}"
assert result2["score_before"] == 0.8, f"score_before: {result2['score_before']}"
assert result2["score_after"] == 0.0, f"score_after: {result2['score_after']}"
assert result2["score_delta"] == 0.8, f"score_delta: {result2['score_delta']}"
assert result2["improved"] is True, f"improved: {result2['improved']}"
assert result2["recovered_from_failure"] is True, f"recovered_from_failure: {result2['recovered_from_failure']}"

print("[TEST PASS] retry effectiveness computed correctly")
