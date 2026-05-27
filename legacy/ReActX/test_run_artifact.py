"""
Tests for run artifact generation.
No LLM, no Docker, no network.
Uses a mock result dict that mirrors run_closed_loop's return value.
"""
import sys
import os
import json
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

from app.artifacts.run_artifact import save_run_artifact

MOCK_RESULT = {
    "success": True,
    "total_steps": 1,
    "retry_triggered": False,
    "failure_type": None,
    "reliability_report": {
        "task": "print 42",
        "success": True,
        "attempts": 1,
        "final_score": 0.0,
        "used_memory": False,
        "memory_examples_count": 0,
    },
    "trajectory": [
        {
            "step": 1,
            "input": "Solve the task.\n\nTask:\nprint 42",
            "traj": {
                "task": "print 42",
                "steps": [
                    {
                        "thought": "solve",
                        "action": "execute_code",
                        "tool": "code_executor",
                        "tool_input": "print 42",
                        "observation": "42",
                        "status": "success",
                        "error": None,
                        "latency": 0.5,
                        "extra": {},
                        "generated_code": "print(42)",
                        "sandbox": {
                            "stdout": "42\n",
                            "stderr": "",
                            "return_code": 0,
                            "timeout": False,
                            "runtime_error": False,
                            "runtime": 0.1,
                        },
                    }
                ],
                "final_answer": "42",
                "num_steps": 1,
                "time": 0.5,
            },
            "eval": {
                "score": 0.0,
                "metrics": {"edit_distance": 0.0},
                "runtime_error": False,
                "no_gt": False,
                "source": "evalforge_engine",
                "failure": {
                    "failure_summary": [],
                    "num_failures": 0,
                    "boundary": {},
                },
            },
        }
    ],
}

MOCK_RETRY_RESULT = {
    "success": True,
    "total_steps": 2,
    "retry_triggered": True,
    "failure_type": None,
    "reliability_report": {
        "task": "sort a list",
        "success": True,
        "attempts": 2,
        "final_score": 0.0,
        "used_memory": True,
        "memory_examples_count": 1,
    },
    "trajectory": [
        {
            "step": 1,
            "input": "Solve the task.\n\nTask:\nsort a list",
            "traj": {
                "task": "sort a list",
                "steps": [
                    {
                        "thought": "solve",
                        "action": "execute_code",
                        "tool": "code_executor",
                        "tool_input": "sort a list",
                        "observation": None,
                        "status": "error",
                        "error": "SyntaxError",
                        "latency": 0.3,
                        "extra": {},
                        "generated_code": "sort([])",
                        "sandbox": {
                            "stdout": "",
                            "stderr": "SyntaxError: invalid syntax",
                            "return_code": 1,
                            "timeout": False,
                            "runtime_error": True,
                            "runtime": 0.05,
                        },
                    }
                ],
                "final_answer": None,
                "num_steps": 1,
                "time": 0.3,
            },
            "eval": {
                "score": 1.0,
                "metrics": {"edit_distance": 1.0},
                "runtime_error": True,
                "no_gt": False,
                "source": "evalforge_engine",
                "failure": {
                    "failure_summary": ["runtime_error"],
                    "num_failures": 1,
                    "boundary": {},
                },
            },
        },
        {
            "step": 2,
            "input": "Fix runtime error...",
            "traj": {
                "task": "sort a list",
                "steps": [
                    {
                        "thought": "fix",
                        "action": "execute_code",
                        "tool": "code_executor",
                        "tool_input": "sort a list",
                        "observation": "[1, 2, 3]",
                        "status": "success",
                        "error": None,
                        "latency": 0.5,
                        "extra": {},
                        "generated_code": "print(sorted([3,1,2]))",
                        "sandbox": {
                            "stdout": "[1, 2, 3]\n",
                            "stderr": "",
                            "return_code": 0,
                            "timeout": False,
                            "runtime_error": False,
                            "runtime": 0.1,
                        },
                    }
                ],
                "final_answer": "[1, 2, 3]",
                "num_steps": 1,
                "time": 0.5,
            },
            "eval": {
                "score": 0.0,
                "metrics": {"edit_distance": 0.0},
                "runtime_error": False,
                "no_gt": False,
                "source": "evalforge_engine",
                "failure": {
                    "failure_summary": [],
                    "num_failures": 0,
                    "boundary": {},
                },
            },
        },
    ],
}

REQUIRED_TOP = {"task", "timestamp", "success", "num_attempts", "final_score", "failure_summary", "memory_used", "attempts"}
REQUIRED_ATTEMPT = {"attempt_index", "generated_code", "stdout", "stderr", "runtime_error", "timeout", "evaluation", "score", "reflection", "retry_reason"}


def test_artifact_file_created():
    with tempfile.TemporaryDirectory() as d:
        path = save_run_artifact(MOCK_RESULT, task="print 42", runs_dir=d)
        assert path is not None
        assert os.path.isfile(path)


def test_artifact_valid_json():
    with tempfile.TemporaryDirectory() as d:
        path = save_run_artifact(MOCK_RESULT, task="print 42", runs_dir=d)
        with open(path) as f:
            json.load(f)  # must not raise


def test_artifact_top_level_fields():
    with tempfile.TemporaryDirectory() as d:
        path = save_run_artifact(MOCK_RESULT, task="print 42", runs_dir=d)
        with open(path) as f:
            data = json.load(f)
        missing = REQUIRED_TOP - set(data.keys())
        assert not missing, f"Missing top-level fields: {missing}"


def test_artifact_attempt_fields():
    with tempfile.TemporaryDirectory() as d:
        path = save_run_artifact(MOCK_RESULT, task="print 42", runs_dir=d)
        with open(path) as f:
            data = json.load(f)
        assert len(data["attempts"]) == 1
        missing = REQUIRED_ATTEMPT - set(data["attempts"][0].keys())
        assert not missing, f"Missing attempt fields: {missing}"


def test_artifact_generated_code_preserved():
    with tempfile.TemporaryDirectory() as d:
        path = save_run_artifact(MOCK_RESULT, task="print 42", runs_dir=d)
        with open(path) as f:
            data = json.load(f)
        assert data["attempts"][0]["generated_code"] == "print(42)"


def test_artifact_stderr_preserved():
    with tempfile.TemporaryDirectory() as d:
        path = save_run_artifact(MOCK_RESULT, task="print 42", runs_dir=d)
        with open(path) as f:
            data = json.load(f)
        assert data["attempts"][0]["stderr"] == ""


def test_artifact_memory_used_false():
    with tempfile.TemporaryDirectory() as d:
        path = save_run_artifact(MOCK_RESULT, task="print 42", runs_dir=d)
        with open(path) as f:
            data = json.load(f)
        assert data["memory_used"] is False


def test_artifact_memory_used_true():
    with tempfile.TemporaryDirectory() as d:
        path = save_run_artifact(MOCK_RETRY_RESULT, task="sort a list", runs_dir=d)
        with open(path) as f:
            data = json.load(f)
        assert data["memory_used"] is True


def test_artifact_filename_format():
    with tempfile.TemporaryDirectory() as d:
        path = save_run_artifact(MOCK_RESULT, task="print 42", runs_dir=d)
        name = os.path.basename(path)
        assert name.startswith("run_"), f"Bad filename: {name}"
        assert name.endswith(".json"), f"Bad extension: {name}"


def test_artifact_is_indented():
    with tempfile.TemporaryDirectory() as d:
        path = save_run_artifact(MOCK_RESULT, task="print 42", runs_dir=d)
        with open(path) as f:
            content = f.read()
        assert "\n  " in content, "JSON is not indented"


def test_retry_attempt_has_reflection():
    with tempfile.TemporaryDirectory() as d:
        path = save_run_artifact(MOCK_RETRY_RESULT, task="sort a list", runs_dir=d)
        with open(path) as f:
            data = json.load(f)
        assert len(data["attempts"]) == 2
        assert data["attempts"][0]["reflection"] is None       # step 1: no reflection
        assert data["attempts"][1]["reflection"] is not None   # step 2: reflection prompt


def test_retry_attempt_retry_reason():
    with tempfile.TemporaryDirectory() as d:
        path = save_run_artifact(MOCK_RETRY_RESULT, task="sort a list", runs_dir=d)
        with open(path) as f:
            data = json.load(f)
        assert data["attempts"][0]["retry_reason"] == "runtime_error"
        assert data["attempts"][1]["retry_reason"] is None  # final success, no retry


def test_broken_result_does_not_crash():
    # Completely broken result — must return None, must not raise
    result = save_run_artifact({"garbage": True}, task="test", runs_dir=tempfile.gettempdir())
    # No assertion on return value — just must not raise


if __name__ == "__main__":
    tests = [
        test_artifact_file_created,
        test_artifact_valid_json,
        test_artifact_top_level_fields,
        test_artifact_attempt_fields,
        test_artifact_generated_code_preserved,
        test_artifact_stderr_preserved,
        test_artifact_memory_used_false,
        test_artifact_memory_used_true,
        test_artifact_filename_format,
        test_artifact_is_indented,
        test_retry_attempt_has_reflection,
        test_retry_attempt_retry_reason,
        test_broken_result_does_not_crash,
    ]
    passed = failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS  {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL  {test.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    if failed:
        sys.exit(1)
