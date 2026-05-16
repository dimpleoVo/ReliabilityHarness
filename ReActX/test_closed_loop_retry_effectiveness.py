"""
Test: retry_effectiveness is returned by run_closed_loop with two attempts.
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

# ── 2. Patch run_evalforge: first call fails, second succeeds ──
import app.loop.closed_loop_runner as _runner_mod

_call_count = {"n": 0}

EVAL_FAIL = {
    "score": 0.8,
    "metrics": {"edit_distance": 0.8},
    "runtime_error": False,
    "no_gt": False,
    "failure": {},
    "source": "evalforge_engine",
}
EVAL_PASS = {
    "score": 0.0,
    "metrics": {"edit_distance": 0.0},
    "runtime_error": False,
    "no_gt": False,
    "failure": {},
    "source": "evalforge_engine",
}


def _fake_evalforge(traj_dict):
    _call_count["n"] += 1
    return EVAL_PASS if _call_count["n"] >= 2 else EVAL_FAIL


_runner_mod.run_evalforge = _fake_evalforge

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
                    "latency": 0.3,
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
assert "retry_effectiveness" in result, "retry_effectiveness missing from result"

re = result["retry_effectiveness"]
assert re["retry_triggered"] is True, f"retry_triggered: {re['retry_triggered']}"
assert re["attempts"] == 2, f"attempts: {re['attempts']}"

print("[TEST PASS] closed-loop retry effectiveness returned correctly")
