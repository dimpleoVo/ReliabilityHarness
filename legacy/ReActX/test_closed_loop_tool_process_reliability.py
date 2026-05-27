"""
Test: tool_process_reliability is returned by run_closed_loop.
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
                    "thought": "compute",
                    "action": "execute_code",
                    "tool": "code_executor",
                    "tool_input": "print(42)",
                    "observation": "42",
                    "status": "success",
                    "error": None,
                    "latency": 0.1,
                    "generated_code": "print(42)",
                    "sandbox": {
                        "runtime_error": False,
                        "return_code": 0,
                        "stdout": "42",
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
assert "tool_process_reliability" in result, "tool_process_reliability missing from result"

tpr = result["tool_process_reliability"]
assert tpr["process_reliability_score"] == 1.0, (
    f"process_reliability_score: {tpr['process_reliability_score']}"
)
assert tpr["unreliable_steps"] == 0, f"unreliable_steps: {tpr['unreliable_steps']}"

rr = result["reliability_report"]
assert rr["tool_process_reliability_score"] == 1.0, (
    f"reliability_report.tool_process_reliability_score: {rr.get('tool_process_reliability_score')}"
)
assert rr["tool_process_unreliable_steps"] == 0, (
    f"reliability_report.tool_process_unreliable_steps: {rr.get('tool_process_unreliable_steps')}"
)

print("[TEST PASS] closed-loop tool process reliability returned correctly")
