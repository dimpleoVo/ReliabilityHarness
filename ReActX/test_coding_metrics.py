"""
Minimal test for compute_coding_execution_metrics.
No LLM, no Docker.
"""
from app.loop.coding_metrics import compute_coding_execution_metrics

# ── Case 1: success with matching output ──
TRAJ_OK = {
    "steps": [
        {
            "sandbox": {
                "runtime_error": False,
                "return_code": 0,
                "stdout": "42\n",
                "stderr": "",
            }
        }
    ]
}

result = compute_coding_execution_metrics(TRAJ_OK, expected_output="42")

assert result["execution_success"] is True, f"execution_success: {result['execution_success']}"
assert result["runtime_error"] is False, f"runtime_error: {result['runtime_error']}"
assert result["return_code"] == 0, f"return_code: {result['return_code']}"
assert result["stdout_match"] is True, f"stdout_match: {result['stdout_match']}"

# ── Case 2: runtime error ──
TRAJ_ERR = {
    "steps": [
        {
            "sandbox": {
                "runtime_error": True,
                "return_code": 1,
                "stdout": "",
                "stderr": "NameError: name 'x' is not defined",
            }
        }
    ]
}

result2 = compute_coding_execution_metrics(TRAJ_ERR, expected_output="42")

assert result2["execution_success"] is False, f"execution_success: {result2['execution_success']}"
assert result2["runtime_error"] is True, f"runtime_error: {result2['runtime_error']}"
assert result2["stdout_match"] is False, f"stdout_match: {result2['stdout_match']}"

print("[TEST PASS] coding execution metrics computed correctly")
