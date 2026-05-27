"""
Minimal test for classify_runtime_failure.
No LLM, no Docker.
"""
from app.loop.failure_taxonomy import classify_runtime_failure

# ── Case 1: sandbox HTTP 502 ──
traj1 = {
    "steps": [{"error": "Sandbox HTTP 502", "observation": "", "status": "error",
                "sandbox": {"stdout": "", "stderr": "", "runtime_error": True}}]
}
r1 = classify_runtime_failure(traj1)
assert r1["primary_failure_type"] == "sandbox_http_error", (
    f"primary: {r1['primary_failure_type']}"
)
assert r1["severity"] == "high", f"severity: {r1['severity']}"

# ── Case 2: ZeroDivisionError in stderr ──
traj2 = {
    "steps": [{"error": None, "observation": "", "status": "error",
                "sandbox": {"stdout": "", "stderr": "ZeroDivisionError: division by zero",
                            "runtime_error": True}}]
}
r2 = classify_runtime_failure(traj2)
assert "runtime_exception" in r2["failure_types"], (
    f"expected runtime_exception in {r2['failure_types']}"
)
assert r2["severity"] == "medium", f"severity: {r2['severity']}"

# ── Case 3: observation mismatch ──
traj3 = {
    "steps": [{"error": None, "observation": "wrong", "status": "success",
                "sandbox": {"stdout": "42", "stderr": "", "runtime_error": False}}]
}
r3 = classify_runtime_failure(traj3)
assert "observation_mismatch" in r3["failure_types"], (
    f"expected observation_mismatch in {r3['failure_types']}"
)

# ── Case 4: fully successful ──
traj4 = {
    "steps": [{"error": None, "observation": "42", "status": "success",
                "sandbox": {"stdout": "42", "stderr": "", "runtime_error": False}}]
}
r4 = classify_runtime_failure(traj4, eval_result={"runtime_error": False})
assert r4["failure_types"] == [], f"expected no failures, got {r4['failure_types']}"
assert r4["severity"] == "none", f"severity: {r4['severity']}"

# ── Case 5: max_retry_exhausted via reliability_report ──
traj5 = {"steps": []}
rr5 = {"success": False, "retry_triggered": True, "attempts": 3}
r5 = classify_runtime_failure(traj5, reliability_report=rr5)
assert "max_retry_exhausted" in r5["failure_types"], (
    f"expected max_retry_exhausted in {r5['failure_types']}"
)
assert r5["severity"] == "high", f"severity: {r5['severity']}"

print("[TEST PASS] runtime failure taxonomy classified correctly")
