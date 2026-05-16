"""
Minimal test for build_reliability_report.
No real LLM, no Docker, no run_closed_loop.
"""
from app.loop.closed_loop_runner import build_reliability_report

FAKE_STEP = {
    "thought": "solve it",
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

TRAJECTORY_ALL = [
    {
        "step": 1,
        "input": "solve",
        "traj": {"steps": [FAKE_STEP], "final_answer": ""},
        "eval": {"score": 0.0, "runtime_error": False},
    },
    {
        "step": 2,
        "input": "retry",
        "traj": {"steps": [FAKE_STEP], "final_answer": "print('hello')"},
        "eval": {"score": 1.0, "runtime_error": False},
    },
]

FINAL_EVAL = {"score": 1.0, "runtime_error": False}
RETRIEVED = [{"task": "print hello", "fixed_code": "print('hello')"}]
MEMORY_CONTEXT = "=== Similar Past Failure-Fix Examples ==="

FAKE_TPR = {
    "total_steps": 1,
    "reliable_steps": 1,
    "unreliable_steps": 0,
    "process_reliability_score": 1.0,
    "issues": [],
}

FAKE_FTAX = {
    "failure_types": ["sandbox_http_error"],
    "primary_failure_type": "sandbox_http_error",
    "severity": "high",
    "evidence": {"sandbox_http_error": "Sandbox HTTP 502"},
}

report = build_reliability_report(
    task="test task",
    success=True,
    trajectory_all=TRAJECTORY_ALL,
    final_eval=FINAL_EVAL,
    retry_triggered=True,
    failure_type=None,
    retrieved=RETRIEVED,
    memory_context=MEMORY_CONTEXT,
    tool_process_reliability=FAKE_TPR,
    failure_taxonomy=FAKE_FTAX,
)

assert report["task"] == "test task", f"task: {report['task']}"
assert report["success"] is True, f"success: {report['success']}"
assert report["attempts"] == 2, f"attempts: {report['attempts']}"
assert report["final_score"] == 1.0, f"final_score: {report['final_score']}"
assert report["error_type"] is None, f"error_type: {report['error_type']}"
assert report["runtime_error"] is False, f"runtime_error: {report['runtime_error']}"
assert report["used_memory"] is True, f"used_memory: {report['used_memory']}"
assert report["memory_examples_count"] == 1, f"memory_examples_count: {report['memory_examples_count']}"
assert report["retry_triggered"] is True, f"retry_triggered: {report['retry_triggered']}"
assert report["trajectory_steps"] == 1, f"trajectory_steps: {report['trajectory_steps']}"
assert report["score_before"] == 0.0, f"score_before: {report['score_before']}"
assert report["score_after"] == 1.0, f"score_after: {report['score_after']}"
assert "tool_process_reliability_score" in report, "missing tool_process_reliability_score"
assert "tool_process_unreliable_steps" in report, "missing tool_process_unreliable_steps"
assert "tool_process_issue_count" in report, "missing tool_process_issue_count"
assert report["tool_process_reliability_score"] == 1.0, f"tool_process_reliability_score: {report['tool_process_reliability_score']}"
assert report["tool_process_unreliable_steps"] == 0, f"tool_process_unreliable_steps: {report['tool_process_unreliable_steps']}"
assert report["tool_process_issue_count"] == 0, f"tool_process_issue_count: {report['tool_process_issue_count']}"
assert report["primary_failure_type"] == "sandbox_http_error", f"primary_failure_type: {report['primary_failure_type']}"
assert report["failure_severity"] == "high", f"failure_severity: {report['failure_severity']}"
assert report["failure_type_count"] == 1, f"failure_type_count: {report['failure_type_count']}"

print("[TEST PASS] reliability_report built correctly")
