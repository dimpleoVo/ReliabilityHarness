"""
Test: coding_metrics is returned by run_closed_loop.
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
            "final_answer": "42",
            "num_steps": 1,
            "steps": [
                {
                    "thought": "compute it",
                    "action": "execute_code",
                    "tool": "code_executor",
                    "tool_input": "print(42)",
                    "observation": "42\n",
                    "status": "success",
                    "error": None,
                    "latency": 0.2,
                    "generated_code": "print(42)",
                    "sandbox": {
                        "runtime_error": False,
                        "return_code": 0,
                        "stdout": "42\n",
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
assert "coding_metrics" in result, "coding_metrics missing from result"

cm = result["coding_metrics"]
assert cm["execution_success"] is True, f"execution_success: {cm['execution_success']}"
assert cm["runtime_error"] is False, f"runtime_error: {cm['runtime_error']}"
assert cm["return_code"] == 0, f"return_code: {cm['return_code']}"
assert cm["stdout"] == "42\n", f"stdout: {cm['stdout']}"

print("[TEST PASS] closed-loop coding metrics returned correctly")
