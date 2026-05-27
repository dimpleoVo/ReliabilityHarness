"""
Test: expected_output is connected to coding_metrics via get_ground_truth.
No real LLM, no Docker, no Chroma, no real dataset.
"""

# ── 1. Patch get_ground_truth ──
import utils.dataset_loader as _loader_mod
_loader_mod.get_ground_truth = lambda task: "42"

import app.loop.closed_loop_runner as _runner_mod
_runner_mod.get_ground_truth = lambda task: "42"

# ── 2. Patch FailureMemoryVectorStore ──
import app.memory.vector_store as _vs_mod


class _FakeVectorStore:
    def __init__(self):
        pass

    def search(self, query, top_k=2):
        return []

    def add(self, item):
        pass


_vs_mod.FailureMemoryVectorStore = _FakeVectorStore
_runner_mod.FailureMemoryVectorStore = _FakeVectorStore

# ── 3. Patch run_evalforge ──
FAKE_EVAL = {
    "score": 0,
    "metrics": {"edit_distance": 0.0},
    "runtime_error": False,
    "no_gt": False,
    "failure": {},
    "source": "evalforge_engine",
}
_runner_mod.run_evalforge = lambda traj_dict: FAKE_EVAL

# ── 4. Patch ReActXAgent.run ──
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
                    "observation": "42\n",
                    "status": "success",
                    "error": None,
                    "latency": 0.1,
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

# ── 5. Run ──
from app.loop.closed_loop_runner import run_closed_loop

result = run_closed_loop("test task")

# ── 6. Assertions ──
cm = result["coding_metrics"]
assert cm["expected_output"] == "42", f"expected_output: {cm['expected_output']}"
assert cm["stdout_match"] is True, f"stdout_match: {cm['stdout_match']}"

print("[TEST PASS] expected_output connected to coding metrics")
