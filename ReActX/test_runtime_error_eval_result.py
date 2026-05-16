"""
Test: sandbox runtime_error is propagated to eval_result in the LLM Judge branch.
No real LLM call — llm_judge is monkeypatched.
"""
import app.eval.llm_judge as _llm_judge_mod
_llm_judge_mod.llm_judge = lambda task, prediction: {"correct": True, "reason": "fake"}

import app.loop.eval_adapter as _eval_adapter_mod
_eval_adapter_mod.get_ground_truth = lambda task: None  # forces no_gt=True → LLM Judge branch

from app.loop.closed_loop_runner import run_evalforge, is_eval_success

FAKE_TRAJ = {
    "task": "print hello world",
    "final_answer": "print('hello world')",
    "num_steps": 1,
    "steps": [
        {
            "thought": "run it",
            "action": "execute_code",
            "tool": "code_executor",
            "tool_input": "print('hello world')",
            "observation": "",
            "status": "error",
            "error": "NameError: name 'x' is not defined",
            "latency": 0.1,
            "generated_code": "print(x)",
            "sandbox": {
                "runtime_error": True,
                "stdout": "",
                "stderr": "NameError: name 'x' is not defined",
            },
        }
    ],
}

eval_result = run_evalforge(FAKE_TRAJ)

assert eval_result["runtime_error"] is True, (
    f"expected runtime_error=True, got {eval_result['runtime_error']}"
)
assert is_eval_success(eval_result) is False, (
    f"expected is_eval_success=False when runtime_error=True"
)

print("[TEST PASS] runtime_error propagated to eval_result")
