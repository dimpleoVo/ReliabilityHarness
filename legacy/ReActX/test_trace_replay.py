"""
Minimal test for replay_trace.
No LLM, no Docker.
"""
from app.loop.trace_replay import replay_trace

FAKE_RESULT = {
    "trajectory": [
        {
            "step": 1,
            "input": "solve it",
            "traj": {
                "task": "print hello",
                "final_answer": "print('hello')",
                "num_steps": 1,
                "steps": [
                    {
                        "thought": "I should print hello.",
                        "action": "execute_code",
                        "tool": "code_executor",
                        "tool_input": "print('hello')",
                        "observation": "hello",
                        "status": "success",
                        "error": None,
                        "latency": 0.25,
                        "generated_code": "print('hello')",
                        "sandbox": {
                            "runtime_error": False,
                            "stdout": "hello",
                            "stderr": "",
                        },
                    }
                ],
            },
            "eval": {
                "score": 0,
                "metrics": {"edit_distance": 0.0},
                "runtime_error": False,
                "source": "evalforge_engine",
            },
        }
    ],
    "reliability_report": {
        "task": "print hello",
        "success": True,
        "attempts": 1,
        "final_score": 0,
        "error_type": None,
        "runtime_error": False,
        "used_memory": True,
        "memory_examples_count": 1,
        "retry_triggered": False,
        "trajectory_steps": 1,
        "score_before": None,
        "score_after": None,
    },
    "reliability_events": [
        {"stage": "memory", "event": "memory_search_started", "status": "info", "details": {}},
        {"stage": "memory", "event": "memory_retrieved", "status": "info", "details": {"count": 1}},
        {"stage": "memory", "event": "memory_injected", "status": "info", "details": {"count": 1}},
        {"stage": "eval", "event": "eval_completed", "status": "pass", "details": {"step": 1}},
        {"stage": "loop", "event": "retry_stopped", "status": "info", "details": {"reason": "success"}},
        {"stage": "memory", "event": "memory_not_saved", "status": "info", "details": {"saved": False}},
    ],
    "tool_reliability": {
        "code_executor": {
            "total_calls": 1,
            "success_calls": 1,
            "runtime_error_calls": 0,
            "success_rate": 1.0,
            "runtime_error_rate": 0.0,
            "avg_latency": 0.25,
        }
    },
    "retry_effectiveness": {
        "retry_triggered": False,
        "attempts": 1,
        "score_before": None,
        "score_after": None,
        "score_delta": None,
        "improved": False,
        "recovered_from_failure": False,
    },
    "coding_metrics": {
        "execution_success": True,
        "runtime_error": False,
        "return_code": 0,
        "stdout": "hello\n",
        "stderr": "",
        "stdout_match": True,
        "expected_output": "hello",
    },
    "tool_process_reliability": {
        "total_steps": 1,
        "reliable_steps": 1,
        "unreliable_steps": 0,
        "process_reliability_score": 1.0,
        "issues": [],
    },
    "failure_taxonomy": {
        "failure_types": ["sandbox_http_error"],
        "primary_failure_type": "sandbox_http_error",
        "severity": "high",
        "evidence": {"sandbox_http_error": "Sandbox HTTP 502"},
    },
}

output = replay_trace(FAKE_RESULT)

assert "TRACE REPLAY" in output, "missing TRACE REPLAY header"
assert "Reliability Summary" in output, "missing Reliability Summary"
assert "Attempt 1" in output, "missing Attempt 1"
assert "Generated Code" in output, "missing Generated Code"
assert "Sandbox Result" in output, "missing Sandbox Result"
assert "Reliability Events" in output, "missing Reliability Events"
assert "memory_retrieved" in output, "missing memory_retrieved event"
assert "Tool Reliability" in output, "missing Tool Reliability section"
assert "code_executor" in output, "missing code_executor in tool reliability"
assert "success_rate" in output, "missing success_rate"
assert "runtime_error_rate" in output, "missing runtime_error_rate"
assert "Retry Effectiveness" in output, "missing Retry Effectiveness section"
assert "retry_triggered" in output, "missing retry_triggered"
assert "score_delta" in output, "missing score_delta"
assert "recovered_from_failure" in output, "missing recovered_from_failure"
assert "Coding Execution Metrics" in output, "missing Coding Execution Metrics section"
assert "execution_success" in output, "missing execution_success"
assert "return_code" in output, "missing return_code"
assert "stdout_match" in output, "missing stdout_match"
assert "Tool Process Reliability" in output, "missing Tool Process Reliability section"
assert "process_reliability_score" in output, "missing process_reliability_score"
assert "unreliable_steps" in output, "missing unreliable_steps"
assert "Failure Taxonomy" in output, "missing Failure Taxonomy section"
assert "primary_failure_type" in output, "missing primary_failure_type"
assert "severity" in output, "missing severity"
assert "sandbox_http_error" in output, "missing sandbox_http_error in failure taxonomy"

print("[TEST PASS] trace replay generated correctly")
