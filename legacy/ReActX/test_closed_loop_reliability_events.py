"""
Integration-level test for reliability_events in run_closed_loop.
No real LLM, no Docker, no Chroma.
"""

# ── 1. Patch FailureMemoryVectorStore before closed_loop_runner is imported ──
import app.memory.vector_store as _vs_mod

FAKE_MEMORY = [{"task": "print hello", "fixed_code": "print('hello')", "bad_code": "", "stderr": ""}]


class _FakeVectorStore:
    def __init__(self):
        pass

    def search(self, query, top_k=2):
        return FAKE_MEMORY

    def add(self, item):
        pass


_vs_mod.FailureMemoryVectorStore = _FakeVectorStore

# ── 2. Patch run_evalforge (module function, patch before import of run_closed_loop) ──
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
from app.agent.trajectory import Trajectory, Step


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
                    "latency": 0.1,
                    "generated_code": "print('hello')",
                    "sandbox": {"runtime_error": False, "stdout": "hello", "stderr": ""},
                }
            ],
        }


import app.agent.react_agent as _agent_mod
_agent_mod.ReActXAgent.run = lambda self, task: _FakeTrajectory()

# ── 4. Also patch FailureMemoryVectorStore inside closed_loop_runner namespace ──
_runner_mod.FailureMemoryVectorStore = _FakeVectorStore

# ── 5. Run ──
from app.loop.closed_loop_runner import run_closed_loop

result = run_closed_loop("test task")

# ── 6. Assertions ──
assert "reliability_events" in result, "reliability_events missing from result"
assert "reliability_report" in result, "reliability_report missing from result"

events = result["reliability_events"]
event_names = {e["event"] for e in events}

REQUIRED_EVENTS = {
    "memory_search_started",
    "memory_retrieved",
    "memory_injected",
    "eval_completed",
    "retry_stopped",
    "memory_not_saved",
}

missing = REQUIRED_EVENTS - event_names
assert not missing, f"Missing events: {missing}. Got: {event_names}"

for e in events:
    for field in ("stage", "event", "status", "details"):
        assert field in e, f"Event missing field '{field}': {e}"

print("[TEST PASS] closed-loop reliability events returned correctly")
