"""
Step 5B: Run Artifact Validation Tests.
No LLM, no Docker, no real closed loop.
Uses a mock result dict that mirrors run_closed_loop's return value.
Run with: python test_run_artifact_generation.py
"""
import sys
import os
import json
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

from app.artifacts.run_artifact import save_run_artifact

# ---------------------------------------------------------------------------
# Shared mock data
# ---------------------------------------------------------------------------

MOCK_RESULT = {
    "success": True,
    "total_steps": 1,
    "retry_triggered": False,
    "failure_type": None,
    "reliability_report": {
        "task": "print hello world",
        "success": True,
        "attempts": 1,
        "final_score": 0.0,
        "used_memory": False,
        "memory_examples_count": 0,
    },
    "trajectory": [
        {
            "step": 1,
            "input": "Solve the task.\n\nTask:\nprint hello world",
            "traj": {
                "task": "print hello world",
                "steps": [
                    {
                        "thought": "I need to write Python that prints hello world",
                        "action": "execute_code",
                        "tool": "code_executor",
                        "tool_input": "print hello world",
                        "observation": "hello world",
                        "status": "success",
                        "error": None,
                        "latency": 0.42,
                        "extra": {},
                        "generated_code": 'print("hello world")',
                        "sandbox": {
                            "stdout": "hello world\n",
                            "stderr": "",
                            "return_code": 0,
                            "timeout": False,
                            "runtime_error": False,
                            "runtime": 0.08,
                        },
                    }
                ],
                "final_answer": "hello world",
                "num_steps": 1,
                "time": 0.42,
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

REQUIRED_TOP_FIELDS = {
    "task", "timestamp", "success", "num_attempts",
    "final_score", "failure_summary", "memory_used", "attempts",
}

REQUIRED_ATTEMPT_FIELDS = {
    "attempt_index", "generated_code", "stdout", "stderr",
    "runtime_error", "timeout", "evaluation", "score",
    "reflection", "retry_reason",
}

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_artifact_file_created():
    with tempfile.TemporaryDirectory() as d:
        path = save_run_artifact(MOCK_RESULT, task="print hello world", runs_dir=d)
        assert path is not None, "save_run_artifact returned None unexpectedly"
        assert os.path.isfile(path), f"Artifact file not found at: {path}"
        assert os.path.basename(path).startswith("run_"), \
            f"Filename does not match run_*.json pattern: {os.path.basename(path)}"
        assert os.path.basename(path).endswith(".json"), \
            f"Filename does not end with .json: {os.path.basename(path)}"


def test_artifact_json_loadable():
    with tempfile.TemporaryDirectory() as d:
        path = save_run_artifact(MOCK_RESULT, task="print hello world", runs_dir=d)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict), "Artifact root must be a JSON object"


def test_artifact_top_level_fields():
    with tempfile.TemporaryDirectory() as d:
        path = save_run_artifact(MOCK_RESULT, task="print hello world", runs_dir=d)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        missing = REQUIRED_TOP_FIELDS - set(data.keys())
        assert not missing, f"Missing top-level fields: {sorted(missing)}"
        assert isinstance(data["attempts"], list), \
            f"'attempts' must be a list, got {type(data['attempts'])}"
        assert len(data["attempts"]) >= 1, \
            f"'attempts' must contain at least one entry, got {len(data['attempts'])}"


def test_artifact_attempt_fields():
    with tempfile.TemporaryDirectory() as d:
        path = save_run_artifact(MOCK_RESULT, task="print hello world", runs_dir=d)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        attempt = data["attempts"][0]
        missing = REQUIRED_ATTEMPT_FIELDS - set(attempt.keys())
        assert not missing, f"Missing attempt fields: {sorted(missing)}"


def test_generated_code_and_stderr_preserved():
    with tempfile.TemporaryDirectory() as d:
        path = save_run_artifact(MOCK_RESULT, task="print hello world", runs_dir=d)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        attempt = data["attempts"][0]
        assert attempt["generated_code"] == 'print("hello world")', \
            f"generated_code was lost or altered: {attempt['generated_code']!r}"
        assert "stderr" in attempt, "stderr field missing from attempt"
        assert attempt["stderr"] == "", \
            f"stderr mismatch: expected '', got {attempt['stderr']!r}"


def test_memory_used_is_bool():
    with tempfile.TemporaryDirectory() as d:
        path = save_run_artifact(MOCK_RESULT, task="print hello world", runs_dir=d)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data["memory_used"], bool), \
            f"memory_used must be bool, got {type(data['memory_used'])}: {data['memory_used']!r}"
        assert data["memory_used"] is False


def test_artifact_write_failure_does_not_crash():
    # Strategy 1: pass a path that cannot be created (a file used as directory).
    with tempfile.NamedTemporaryFile(suffix=".file", delete=False) as tmp:
        bad_dir = tmp.name  # this is a file, not a directory — makedirs will fail

    try:
        result = save_run_artifact(MOCK_RESULT, task="test", runs_dir=bad_dir)
        # Must return None (or a path) — must NOT raise
        # We don't assert a specific value; the guarantee is just "no exception"
    finally:
        os.unlink(bad_dir)

    # Strategy 2: corrupted result dict — no 'trajectory' key.
    result2 = save_run_artifact({"totally": "broken"}, task="test",
                                runs_dir=tempfile.gettempdir())
    # Again: must not raise; return value is not the contract being tested here.


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [
        test_artifact_file_created,
        test_artifact_json_loadable,
        test_artifact_top_level_fields,
        test_artifact_attempt_fields,
        test_generated_code_and_stderr_preserved,
        test_memory_used_is_bool,
        test_artifact_write_failure_does_not_crash,
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
        except Exception as e:
            print(f"ERROR {test.__name__}: {type(e).__name__}: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    if failed:
        sys.exit(1)
