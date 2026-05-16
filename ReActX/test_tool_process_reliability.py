"""
Minimal test for check_tool_process_reliability.
No LLM, no Docker.
"""
from app.loop.tool_process_reliability import check_tool_process_reliability

# ── Case 1: perfect step, score should be 1.0 ──
TRAJ_OK = {
    "steps": [
        {
            "tool": "code_executor",
            "tool_input": "print(42)",
            "observation": "42",
            "generated_code": "print(42)",
            "status": "success",
            "sandbox": {
                "runtime_error": False,
                "stdout": "42",
                "stderr": "",
            },
        }
    ]
}

result = check_tool_process_reliability(TRAJ_OK)
assert result["process_reliability_score"] == 1.0, (
    f"expected 1.0, got {result['process_reliability_score']}"
)
assert result["issues"] == [], f"expected no issues, got {result['issues']}"

# ── Case 2: observation mismatch + runtime_error_status_mismatch ──
TRAJ_BAD = {
    "steps": [
        {
            "tool": "code_executor",
            "tool_input": "print(42)",
            "observation": "wrong",
            "generated_code": "print(42)",
            "status": "success",
            "sandbox": {
                "runtime_error": True,
                "stdout": "42",
                "stderr": "Error",
            },
        }
    ]
}

result2 = check_tool_process_reliability(TRAJ_BAD)
issue_types = {issue["issue_type"] for issue in result2["issues"]}

assert "observation_mismatch" in issue_types, (
    f"expected observation_mismatch in issues, got {issue_types}"
)
assert "runtime_error_status_mismatch" in issue_types, (
    f"expected runtime_error_status_mismatch in issues, got {issue_types}"
)
assert result2["process_reliability_score"] == 0.0, (
    f"expected 0.0, got {result2['process_reliability_score']}"
)

print("[TEST PASS] tool process reliability checked correctly")
