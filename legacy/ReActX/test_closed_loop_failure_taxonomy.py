"""
Test: failure_taxonomy is returned by run_closed_loop.
No real LLM, no Docker, no Chroma.
"""

# ── 1. Patch FailureMemoryVectorStore ──
import app.memory.vector_store as _vs_mod


class _FakeVectorStore:
    def __init__(self):
        pass

    def search(self, query, top_k=2):
        return []

    def add(self, item):
        pass


_vs_mod.FailureMemoryVectorStore = _FakeVectorStore

# ── 2. Patch run_evalforge: returns failure with runtime_error ──
import app.loop.closed_loop_runner as _runner_mod

FAKE_EVAL_FAIL = {
    "score": 1.0,
    "metrics": {"edit_distance": 1.0},
    "runtime_error": True,
    "no_gt": False,
    "failure": {"failure_summary": ["runtime_error"]},
    "source": "evalforge_engine",
}

_call_count = {"n": 0}


def _fake_evalforge(traj_dict):
    return FAKE_EVAL_FAIL


_runner_mod.run_evalforge = _fake_evalforge

# ── 3. Patch ReActXAgent.run: returns failing trajectory ──
class _FakeTrajectory:
    def to_dict(self):
        return {
            "task": "test task",
            "final_answer": "",
            "num_steps": 1,
            "steps": [
                {
                    "thought": "run it",
                    "action": "execute_code",
                    "tool": "code_executor",
                    "tool_input": "print(42)",
                    "observation": "",
                    "status": "error",
                    "error": "Sandbox HTTP 502",
                    "latency": 0.1,
                    "generated_code": "print(42)",
                    "sandbox": {
                        "runtime_error": True,
                        "return_code": 1,
                        "stdout": "",
                        "stderr": "",
                    },
                }
            ],
        }


import app.agent.react_agent as _agent_mod
_agent_mod.ReActXAgent.run = lambda self, task: _FakeTrajectory()

_runner_mod.FailureMemoryVectorStore = _FakeVectorStore

# ── 4. Run ──
from app.loop.closed_loop_runner import run_closed_loop

result = run_closed_loop("test task")

# ── 5. Assertions ──
assert "failure_taxonomy" in result, "failure_taxonomy missing from result"

ft = result["failure_taxonomy"]
assert ft["primary_failure_type"] == "sandbox_http_error", (
    f"primary_failure_type: {ft['primary_failure_type']}"
)
assert ft["severity"] == "high", f"severity: {ft['severity']}"

rr = result["reliability_report"]
assert rr["primary_failure_type"] == "sandbox_http_error", (
    f"reliability_report.primary_failure_type: {rr.get('primary_failure_type')}"
)
assert rr["failure_severity"] == "high", (
    f"reliability_report.failure_severity: {rr.get('failure_severity')}"
)
assert rr["success"] is False, f"reliability_report.success: {rr.get('success')}"
assert rr["attempts"] == 3, f"reliability_report.attempts: {rr.get('attempts')}"

assert "max_retry_exhausted" in ft["failure_types"], (
    f"expected max_retry_exhausted in failure_types: {ft['failure_types']}"
)
assert ft["severity"] == "high", f"post-recompute severity: {ft['severity']}"

print("[TEST PASS] closed-loop failure taxonomy returned correctly")
