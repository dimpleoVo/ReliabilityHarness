"""
Step 6: Reliability Report Generator tests.
Tests app/reporting/reliability_report.py — the artifact-to-report pipeline.
No LLM, no Docker, no real closed loop.
Run with: python test_reporting_module.py
"""
import sys
import os
import json
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

from app.reporting.reliability_report import (
    load_artifacts,
    compute_metrics,
    generate_report,
    render_markdown,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def _attempt(idx=1, runtime_error=False, timeout=False, retry_reason=None,
             stdout="1\n", stderr=""):
    return {
        "attempt_index": idx,
        "generated_code": f"print({idx})",
        "stdout": stdout,
        "stderr": stderr,
        "runtime_error": runtime_error,
        "timeout": timeout,
        "score": 0.0 if not runtime_error else 1.0,
        "evaluation": {},
        "reflection": None if idx == 1 else "Fix...",
        "retry_reason": retry_reason,
    }


# 4 run artifacts covering all metric scenarios
RUN_OK = {
    "task": "print 42", "success": True, "num_attempts": 1,
    "memory_used": False, "failure_summary": [],
    "attempts": [_attempt(idx=1)],
}

RUN_RUNTIME_THEN_OK = {
    "task": "sort list", "success": True, "num_attempts": 2,
    "memory_used": True, "failure_summary": ["runtime_error"],
    "attempts": [
        _attempt(idx=1, runtime_error=True, retry_reason="runtime_error", stdout="", stderr="NameError"),
        _attempt(idx=2, stdout="[1,2,3]\n"),
    ],
}

RUN_SEMANTIC_FAIL = {
    "task": "fibonacci", "success": False, "num_attempts": 2,
    "memory_used": False, "failure_summary": ["semantic_error"],
    "attempts": [
        _attempt(idx=1, retry_reason="semantic_error", stdout="wrong\n"),
        _attempt(idx=2, retry_reason="semantic_error", stdout="wrong2\n"),
    ],
}

RUN_TIMEOUT = {
    "task": "infinite loop", "success": False, "num_attempts": 1,
    "memory_used": False, "failure_summary": [],
    "attempts": [
        _attempt(idx=1, runtime_error=True, timeout=True,
                 retry_reason="runtime_error", stdout="", stderr="Timed out"),
    ],
}

ALL_FOUR = [RUN_OK, RUN_RUNTIME_THEN_OK, RUN_SEMANTIC_FAIL, RUN_TIMEOUT]

# Expected values for ALL_FOUR (pre-computed):
# total=4, success=2, success_rate=0.5
# avg_attempts=(1+2+2+1)/4=1.5
# all_attempts=6, runtime_error_count=2, timeout_count=1
# runtime_error_rate=2/6≈0.3333, timeout_rate=1/6≈0.1667
# memory_usage_rate=1/4=0.25
# retry_trigger_rate=2/4=0.5
# recovered=1 (RUN_RUNTIME_THEN_OK), recovery_rate=1/4=0.25
# dist={runtime_error:1, semantic_error:2, timeout:1, unknown:0}


def _write_runs(runs_dir, artifacts):
    """Write a list of artifact dicts to run_*.json files in runs_dir."""
    for i, art in enumerate(artifacts):
        path = os.path.join(runs_dir, f"run_2026051700{i:04d}.json")
        with open(path, "w") as f:
            json.dump(art, f)


# ---------------------------------------------------------------------------
# 1. Empty runs/ does not crash
# ---------------------------------------------------------------------------

def test_empty_runs_does_not_crash():
    with tempfile.TemporaryDirectory() as d:
        arts = load_artifacts(d)
        assert arts == []
        m = compute_metrics(arts)
        assert m["total_runs"] == 0
        assert m["success_rate"] == 0.0
        assert isinstance(m["failure_type_distribution"], dict)


# ---------------------------------------------------------------------------
# 2. Single artifact aggregation
# ---------------------------------------------------------------------------

def test_single_artifact_aggregation():
    m = compute_metrics([RUN_OK])
    assert m["total_runs"] == 1
    assert m["success_rate"] == 1.0
    assert m["avg_attempts"] == 1.0
    assert m["memory_usage_rate"] == 0.0
    assert m["retry_trigger_rate"] == 0.0
    assert m["recovery_rate"] == 0.0
    assert m["runtime_error_rate"] == 0.0
    assert m["timeout_rate"] == 0.0


# ---------------------------------------------------------------------------
# 3. Multiple artifacts aggregation
# ---------------------------------------------------------------------------

def test_multiple_artifacts_aggregation():
    m = compute_metrics(ALL_FOUR)
    assert m["total_runs"] == 4
    assert m["success_rate"] == 0.5
    assert m["avg_attempts"] == 1.5
    assert m["memory_usage_rate"] == 0.25
    assert m["retry_trigger_rate"] == 0.5


# ---------------------------------------------------------------------------
# 4. runtime_error_rate
# ---------------------------------------------------------------------------

def test_runtime_error_rate_correct():
    m = compute_metrics(ALL_FOUR)
    expected = round(2 / 6, 4)
    assert abs(m["runtime_error_rate"] - expected) < 1e-6, (
        f"runtime_error_rate: expected {expected}, got {m['runtime_error_rate']}"
    )


# ---------------------------------------------------------------------------
# 5. timeout_rate
# ---------------------------------------------------------------------------

def test_timeout_rate_correct():
    m = compute_metrics(ALL_FOUR)
    expected = round(1 / 6, 4)
    assert abs(m["timeout_rate"] - expected) < 1e-6, (
        f"timeout_rate: expected {expected}, got {m['timeout_rate']}"
    )


# ---------------------------------------------------------------------------
# 6. recovery_rate
# ---------------------------------------------------------------------------

def test_recovery_rate_correct():
    m = compute_metrics(ALL_FOUR)
    assert m["recovery_rate"] == 0.25, (
        f"recovery_rate: expected 0.25, got {m['recovery_rate']}"
    )


# ---------------------------------------------------------------------------
# 7. failure_type_distribution
# ---------------------------------------------------------------------------

def test_failure_type_distribution_correct():
    m = compute_metrics(ALL_FOUR)
    dist = m["failure_type_distribution"]
    assert dist["runtime_error"] == 1,  f"runtime_error: {dist['runtime_error']}"
    assert dist["semantic_error"] == 2, f"semantic_error: {dist['semantic_error']}"
    assert dist["timeout"] == 1,        f"timeout: {dist['timeout']}"
    assert dist["unknown"] == 0,        f"unknown: {dist['unknown']}"


# ---------------------------------------------------------------------------
# 8. Markdown report generated
# ---------------------------------------------------------------------------

def test_markdown_report_generated():
    with tempfile.TemporaryDirectory() as runs_d, \
         tempfile.TemporaryDirectory() as rep_d:
        _write_runs(runs_d, [RUN_OK, RUN_RUNTIME_THEN_OK])
        generate_report(runs_dir=runs_d, reports_dir=rep_d)

        md_path = os.path.join(rep_d, "reliability_report.md")
        assert os.path.isfile(md_path), "reliability_report.md not created"

        with open(md_path) as f:
            content = f.read()

        for expected in [
            "# Reliability Report",
            "Success Rate",
            "Runtime Error Rate",
            "Failure Type Distribution",
            "Total Runs",
        ]:
            assert expected in content, f"Missing section: {expected!r}"


# ---------------------------------------------------------------------------
# 9. JSON report generated
# ---------------------------------------------------------------------------

def test_json_report_generated():
    with tempfile.TemporaryDirectory() as runs_d, \
         tempfile.TemporaryDirectory() as rep_d:
        _write_runs(runs_d, ALL_FOUR)
        metrics = generate_report(runs_dir=runs_d, reports_dir=rep_d)

        json_path = os.path.join(rep_d, "reliability_report.json")
        assert os.path.isfile(json_path), "reliability_report.json not created"

        with open(json_path) as f:
            data = json.load(f)

        required = {
            "total_runs", "success_rate", "avg_attempts",
            "runtime_error_rate", "timeout_rate", "memory_usage_rate",
            "retry_trigger_rate", "recovery_rate", "failure_type_distribution",
        }
        missing = required - set(data.keys())
        assert not missing, f"Missing JSON fields: {sorted(missing)}"
        assert data["total_runs"] == 4


# ---------------------------------------------------------------------------
# Extras (robustness)
# ---------------------------------------------------------------------------

def test_empty_runs_dir_writes_zero_state_reports():
    with tempfile.TemporaryDirectory() as runs_d, \
         tempfile.TemporaryDirectory() as rep_d:
        metrics = generate_report(runs_dir=runs_d, reports_dir=rep_d)
        assert metrics["total_runs"] == 0
        assert os.path.isfile(os.path.join(rep_d, "reliability_report.json"))
        assert os.path.isfile(os.path.join(rep_d, "reliability_report.md"))


def test_malformed_artifact_files_are_skipped():
    with tempfile.TemporaryDirectory() as runs_d, \
         tempfile.TemporaryDirectory() as rep_d:
        good = os.path.join(runs_d, "run_20260517000001.json")
        with open(good, "w") as f:
            json.dump(RUN_OK, f)
        bad = os.path.join(runs_d, "run_20260517000002.json")
        with open(bad, "w") as f:
            f.write("INVALID {{{{")

        artifacts = load_artifacts(runs_d)
        assert len(artifacts) == 1
        assert artifacts[0]["task"] == "print 42"


def test_unknown_failure_type_counted():
    run_unknown = {
        "task": "mystery", "success": False, "num_attempts": 1,
        "memory_used": False, "failure_summary": [],
        "attempts": [{
            "attempt_index": 1, "generated_code": "pass",
            "stdout": "", "stderr": "", "runtime_error": False,
            "timeout": False, "score": None, "evaluation": {},
            "reflection": None, "retry_reason": None,
        }],
    }
    m = compute_metrics([run_unknown])
    assert m["failure_type_distribution"]["unknown"] == 1


def test_missing_artifact_fields_do_not_crash():
    m = compute_metrics([{"task": "bare_minimum"}])
    assert m["total_runs"] == 1
    assert m["success_rate"] == 0.0
    assert isinstance(m["failure_type_distribution"], dict)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [
        test_empty_runs_does_not_crash,
        test_single_artifact_aggregation,
        test_multiple_artifacts_aggregation,
        test_runtime_error_rate_correct,
        test_timeout_rate_correct,
        test_recovery_rate_correct,
        test_failure_type_distribution_correct,
        test_markdown_report_generated,
        test_json_report_generated,
        test_empty_runs_dir_writes_zero_state_reports,
        test_malformed_artifact_files_are_skipped,
        test_unknown_failure_type_counted,
        test_missing_artifact_fields_do_not_crash,
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
