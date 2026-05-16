"""
Minimal test for compute_tool_reliability.
No LLM, no Docker.
"""
from app.loop.tool_reliability import compute_tool_reliability

FAKE_TRAJECTORY_ALL = [
    {
        "step": 1,
        "traj": {
            "steps": [
                {
                    "tool": "code_executor",
                    "status": "success",
                    "latency": 1.0,
                    "sandbox": {"runtime_error": False},
                }
            ]
        },
    },
    {
        "step": 2,
        "traj": {
            "steps": [
                {
                    "tool": "code_executor",
                    "status": "success",
                    "latency": 2.0,
                    "sandbox": {"runtime_error": False},
                }
            ]
        },
    },
    {
        "step": 3,
        "traj": {
            "steps": [
                {
                    "tool": "code_executor",
                    "status": "error",
                    "latency": 3.0,
                    "sandbox": {"runtime_error": True},
                }
            ]
        },
    },
]

report = compute_tool_reliability(FAKE_TRAJECTORY_ALL)

assert "code_executor" in report, "code_executor missing from report"
ce = report["code_executor"]

assert ce["total_calls"] == 3, f"total_calls: {ce['total_calls']}"
assert ce["success_calls"] == 2, f"success_calls: {ce['success_calls']}"
assert ce["runtime_error_calls"] == 1, f"runtime_error_calls: {ce['runtime_error_calls']}"
assert abs(ce["success_rate"] - 0.667) < 0.001, f"success_rate: {ce['success_rate']}"
assert abs(ce["runtime_error_rate"] - 0.333) < 0.001, f"runtime_error_rate: {ce['runtime_error_rate']}"
assert ce["avg_latency"] == 2.0, f"avg_latency: {ce['avg_latency']}"

print("[TEST PASS] tool reliability computed correctly")
