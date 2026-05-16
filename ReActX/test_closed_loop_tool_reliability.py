"""
Test: tool_reliability is returned by run_closed_loop.
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

# ── 2. Patch run_evalforge ──
import app.loop.closed_loop_runner as _runner_mod

FAKE_EVAL = {
    "score": 0,
    "metrics": {"edit_distance": 0.0},
    "runtime_error": False,
    "no_gt": False,
    "failure": {},
    "source": "evalforge_engine",
}

_runner_mod.run_evalforge = lambda traj_dict: FAKE_EVAL

# ── 3. Patch ReActXAgent.run ──
class _FakeTrajectory:
    def to_dict(self):
        return {
            "task": "test task",
            "final_answer": "print('hello')",
            "num_steps": 1,
            "steps": [
                {
                    "thought": "run it",
                    "action": "execute_code",
                    "tool": "code_executor",
                    "tool_input": "print('hello')",
                    "observation": "hello",
                    "status": "success",
                    "error": None,
                    "latency": 0.5,
                    "generated_code": "print('hello')",
                    "sandbox": {"runtime_error": False, "stdout": "hello", "stderr": ""},
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
assert "tool_reliability" in result, "tool_reliability missing from result"

tr = result["tool_reliability"]
assert "code_executor" in tr, f"code_executor missing; got keys: {list(tr.keys())}"

ce = tr["code_executor"]
assert ce["total_calls"] == 1, f"total_calls: {ce['total_calls']}"
assert ce["success_calls"] == 1, f"success_calls: {ce['success_calls']}"
assert ce["runtime_error_calls"] == 0, f"runtime_error_calls: {ce['runtime_error_calls']}"

print("[TEST PASS] closed-loop tool reliability returned correctly")
