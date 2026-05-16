"""
Minimal test: trajectory steps attached to EvalForge sample meta.
get_ground_truth is monkeypatched so no real dataset file is needed.
"""
import app.loop.eval_adapter as _eval_adapter_mod
_eval_adapter_mod.get_ground_truth = lambda task: "hello world"

from app.loop.eval_adapter import trajectory_to_eval_sample
from app.eval.failure_analyzer import FailureAnalyzer

FAKE_TRAJ = {
    "task": "print hello world",
    "final_answer": "print('hello world')",
    "num_steps": 1,
    "steps": [
        {
            "thought": "I should execute a print statement.",
            "action": "execute_code",
            "tool": "code_executor",
            "tool_input": "print('hello world')",
            "observation": "hello world",
            "status": "success",
            "error": None,
            "latency": 0.42,
            "generated_code": "print('hello world')",
            "sandbox": {"runtime_error": False, "stdout": "hello world", "stderr": ""},
        }
    ],
}

sample = trajectory_to_eval_sample(FAKE_TRAJ)

meta = sample.get("meta", {})
traj_steps = meta.get("trajectory_steps")

assert traj_steps is not None, "trajectory_steps missing from sample meta"
assert len(traj_steps) == 1, f"expected 1 step, got {len(traj_steps)}"

step = traj_steps[0]
assert step["generated_code"] == "print('hello world')", "generated_code mismatch"
assert step["sandbox"] == {"runtime_error": False, "stdout": "hello world", "stderr": ""}, "sandbox mismatch"
assert step["error"] is None, "error should be None"
assert step["latency"] == 0.42, "latency mismatch"

# FailureAnalyzer 读取 trajectory_steps
fa = FailureAnalyzer()
fake_eval = {"runtime_error": False, "score": 0, "source": "evalforge_engine", "no_gt": False}
result = fa.analyze(sample, fake_eval)
assert result is not None

print("[TEST PASS] trajectory steps attached to EvalForge meta")
