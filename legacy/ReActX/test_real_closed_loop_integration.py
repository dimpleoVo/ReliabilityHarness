"""
Real closed-loop integration test.
Requires: DEEPSEEK_API_KEY + running sandbox.

Run:
    DEEPSEEK_API_KEY=<key> python test_real_closed_loop_integration.py
    DEEPSEEK_API_KEY=<key> SANDBOX_URL=http://sandbox:9000 python test_real_closed_loop_integration.py
"""
import os
import sys

# ── Guard: API key ──
if not os.environ.get("DEEPSEEK_API_KEY"):
    print("[SKIP] DEEPSEEK_API_KEY not set")
    sys.exit(0)

# ── Guard: sandbox availability (preflight via /health) ──
import requests

sandbox_url = os.environ.get("SANDBOX_URL", "http://localhost:9000")

try:
    _resp = requests.get(f"{sandbox_url}/health", timeout=5)
    _resp.raise_for_status()
except Exception as e:
    print(f"[SKIP] sandbox service not available: {sandbox_url} ({e})")
    sys.exit(0)

# ── Run closed loop ──
from app.loop.closed_loop_runner import run_closed_loop
from app.loop.trace_replay import replay_trace

TASK = "Write Python code that prints 42."

result = run_closed_loop(TASK)

# ── Assert top-level fields ──
for field in ("trajectory", "reliability_report", "reliability_events",
              "coding_metrics", "tool_reliability", "retry_effectiveness"):
    assert field in result, f"missing field: {field}"

# ── Assert trajectory has at least one step with generated_code containing print ──
traj_all = result["trajectory"]
assert traj_all, "trajectory is empty"

last_traj = traj_all[-1]["traj"]
steps = last_traj.get("steps") or []
assert steps, "no steps in last trajectory"

last_step = steps[-1]
generated_code = last_step.get("generated_code") or ""
assert "print" in generated_code, (
    f"expected 'print' in generated_code, got: {generated_code!r}"
)

sandbox = last_step.get("sandbox") or {}
stdout = sandbox.get("stdout") or ""
assert "42" in str(stdout), (
    f"expected '42' in sandbox stdout, got: {stdout!r}"
)

# ── Assert coding_metrics ──
cm = result["coding_metrics"]
assert cm["execution_success"] is True, f"execution_success: {cm['execution_success']}"
assert cm["runtime_error"] is False, f"runtime_error: {cm['runtime_error']}"

# ── Assert reliability_report exists ──
assert result["reliability_report"], "reliability_report is empty"

# ── Assert reliability_events non-empty ──
assert result["reliability_events"], "reliability_events is empty"

# ── Assert tool_reliability has code_executor ──
assert "code_executor" in result["tool_reliability"], (
    f"code_executor missing from tool_reliability: {list(result['tool_reliability'].keys())}"
)

# ── Assert trace replay ──
replay = replay_trace(result)

for section in ("TRACE REPLAY", "Coding Execution Metrics", "Tool Reliability", "Reliability Events"):
    assert section in replay, f"replay missing section: {section!r}"

print("[TEST PASS] real closed-loop integration passed")
