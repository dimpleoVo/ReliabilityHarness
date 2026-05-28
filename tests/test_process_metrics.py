"""Tests for Benchmark-5A — minimal observable process metrics.

No LLM calls. No Docker. No memory/retry.

Covered:
1.  all success -> observable_process_success True
2.  extraction failed -> process_failure_stage extraction
3.  has_extracted_code False -> process_failure_stage extraction
4.  execution not performed -> process_failure_stage execution
5.  timeout -> timeout_observed True and process_failure_stage execution
6.  runtime_error -> runtime_error_observed True and process_failure_stage execution
7.  tests failed -> observable_process_success False
8.  missing generation/execution fields -> process_failure_stage unknown
9.  metrics include fixed field set
10. is_full_process_reliability_metric is False
11. no LLM/Docker/retry/memory imports or calls
"""
from __future__ import annotations

from reliability_harness.metrics.process_metrics import (
    compute_minimal_process_metrics,
    compute_minimal_process_metrics_from_sections,
)


# ── Fixtures ───────────────────────────────────────────────────────────────────

def _gen(
    *,
    extraction_status: str = "success",
    has_extracted_code: bool = True,
) -> dict:
    return {
        "extraction_status": extraction_status,
        "has_extracted_code": has_extracted_code,
    }


def _exec(
    *,
    execution_performed: bool = True,
    tests_passed: bool = True,
    error_type: str | None = None,
    timed_out: bool = False,
) -> dict:
    return {
        "execution_performed": execution_performed,
        "tests_passed": tests_passed,
        "error_type": error_type,
        "timed_out": timed_out,
    }


def _m(gen=None, exc=None) -> dict:
    g = gen if gen is not None else _gen()
    e = exc if exc is not None else _exec()
    return compute_minimal_process_metrics_from_sections(g, e)


# ── 1. All success → observable_process_success True ──────────────────────────

class TestAllSuccess:
    def test_observable_process_success_true(self):
        assert _m()["observable_process_success"] is True

    def test_process_failure_stage_completed(self):
        assert _m()["process_failure_stage"] == "completed"

    def test_positive_pipeline_flags(self):
        m = _m()
        assert m["generation_completed"] is True
        assert m["code_extraction_success"] is True
        assert m["execution_attempted"] is True
        assert m["execution_completed"] is True
        assert m["execution_success"] is True

    def test_no_error_flags(self):
        m = _m()
        assert m["timeout_observed"] is False
        assert m["runtime_error_observed"] is False


# ── 2. Extraction failed → process_failure_stage extraction ───────────────────

class TestExtractionFailed:
    def test_stage_is_extraction(self):
        m = _m(gen=_gen(extraction_status="failed", has_extracted_code=False))
        assert m["process_failure_stage"] == "extraction"

    def test_observable_process_success_false(self):
        m = _m(gen=_gen(extraction_status="failed", has_extracted_code=False))
        assert m["observable_process_success"] is False

    def test_code_extraction_success_false(self):
        m = _m(gen=_gen(extraction_status="failed", has_extracted_code=False))
        assert m["code_extraction_success"] is False

    def test_generation_completed_still_true(self):
        m = _m(gen=_gen(extraction_status="failed", has_extracted_code=False))
        assert m["generation_completed"] is True


# ── 3. has_extracted_code False → process_failure_stage extraction ────────────

class TestHasExtractedCodeFalse:
    def test_status_success_but_no_code_gives_extraction_stage(self):
        m = _m(gen=_gen(extraction_status="success", has_extracted_code=False))
        assert m["process_failure_stage"] == "extraction"

    def test_code_extraction_success_false(self):
        m = _m(gen=_gen(extraction_status="success", has_extracted_code=False))
        assert m["code_extraction_success"] is False

    def test_observable_process_success_false(self):
        m = _m(gen=_gen(extraction_status="success", has_extracted_code=False))
        assert m["observable_process_success"] is False


# ── 4. Execution not performed → process_failure_stage execution ──────────────

class TestExecutionNotPerformed:
    def test_stage_is_execution(self):
        m = _m(exc=_exec(execution_performed=False, tests_passed=False))
        assert m["process_failure_stage"] == "execution"

    def test_execution_attempted_false(self):
        m = _m(exc=_exec(execution_performed=False, tests_passed=False))
        assert m["execution_attempted"] is False

    def test_observable_process_success_false(self):
        m = _m(exc=_exec(execution_performed=False, tests_passed=False))
        assert m["observable_process_success"] is False


# ── 5. Timeout → timeout_observed True and process_failure_stage execution ────

class TestTimeout:
    def _timeout_metrics(self):
        return _m(exc=_exec(
            execution_performed=True,
            tests_passed=False,
            error_type="timeout",
            timed_out=True,
        ))

    def test_timeout_observed_true(self):
        assert self._timeout_metrics()["timeout_observed"] is True

    def test_stage_is_execution(self):
        assert self._timeout_metrics()["process_failure_stage"] == "execution"

    def test_execution_completed_false(self):
        assert self._timeout_metrics()["execution_completed"] is False

    def test_observable_process_success_false(self):
        assert self._timeout_metrics()["observable_process_success"] is False


# ── 6. runtime_error → runtime_error_observed True and execution stage ────────

class TestRuntimeError:
    def _runtime_error_metrics(self):
        return _m(exc=_exec(
            execution_performed=True,
            tests_passed=False,
            error_type="runtime_error",
            timed_out=False,
        ))

    def test_runtime_error_observed_true(self):
        assert self._runtime_error_metrics()["runtime_error_observed"] is True

    def test_stage_is_execution(self):
        assert self._runtime_error_metrics()["process_failure_stage"] == "execution"

    def test_observable_process_success_false(self):
        assert self._runtime_error_metrics()["observable_process_success"] is False

    def test_timeout_observed_false(self):
        assert self._runtime_error_metrics()["timeout_observed"] is False


# ── 7. Tests failed → observable_process_success False ───────────────────────

class TestTestsFailed:
    def _fail_metrics(self):
        return _m(exc=_exec(
            execution_performed=True,
            tests_passed=False,
            error_type="assertion_failure",
            timed_out=False,
        ))

    def test_observable_process_success_false(self):
        assert self._fail_metrics()["observable_process_success"] is False

    def test_stage_is_execution(self):
        assert self._fail_metrics()["process_failure_stage"] == "execution"

    def test_execution_success_false(self):
        assert self._fail_metrics()["execution_success"] is False

    def test_execution_attempted_true(self):
        assert self._fail_metrics()["execution_attempted"] is True


# ── 8. Missing generation/execution fields → process_failure_stage unknown ────

class TestMissingFields:
    def test_empty_dicts_give_unknown(self):
        m = compute_minimal_process_metrics_from_sections({}, {})
        assert m["process_failure_stage"] == "unknown"

    def test_empty_dicts_observable_false(self):
        m = compute_minimal_process_metrics_from_sections({}, {})
        assert m["observable_process_success"] is False

    def test_none_sections_give_unknown(self):
        m = compute_minimal_process_metrics({"generation": None, "execution": None})
        assert m["process_failure_stage"] == "unknown"

    def test_missing_summary_sections_give_unknown(self):
        m = compute_minimal_process_metrics({})
        assert m["process_failure_stage"] == "unknown"

    def test_non_dict_input_gives_unknown(self):
        m = compute_minimal_process_metrics_from_sections("bad", 42)
        assert m["process_failure_stage"] == "unknown"

    def test_generation_completed_false_when_no_extraction_status(self):
        m = compute_minimal_process_metrics_from_sections(
            {"has_extracted_code": True}, _exec()
        )
        assert m["generation_completed"] is False
        assert m["process_failure_stage"] == "unknown"


# ── 9. Metrics include fixed field set ────────────────────────────────────────

class TestFixedFieldSet:
    _EXPECTED_KEYS = {
        "generation_completed",
        "code_extraction_success",
        "execution_attempted",
        "execution_completed",
        "execution_success",
        "timeout_observed",
        "runtime_error_observed",
        "process_failure_stage",
        "observable_process_success",
        "is_full_process_reliability_metric",
        "definition",
    }

    def test_all_expected_keys_present_success(self):
        assert set(_m().keys()) == self._EXPECTED_KEYS

    def test_all_expected_keys_present_unknown(self):
        m = compute_minimal_process_metrics_from_sections({}, {})
        assert set(m.keys()) == self._EXPECTED_KEYS

    def test_definition_is_nonempty_string(self):
        assert isinstance(_m()["definition"], str)
        assert len(_m()["definition"]) > 0

    def test_process_failure_stage_valid_enum(self):
        valid = {"generation", "extraction", "execution", "completed", "unknown"}
        assert _m()["process_failure_stage"] in valid

    def test_process_failure_stage_unknown_in_valid_enum(self):
        valid = {"generation", "extraction", "execution", "completed", "unknown"}
        m = compute_minimal_process_metrics_from_sections({}, {})
        assert m["process_failure_stage"] in valid


# ── 10. is_full_process_reliability_metric is always False ───────────────────

class TestIsFullProcessReliabilityMetric:
    def test_false_on_success(self):
        assert _m()["is_full_process_reliability_metric"] is False

    def test_false_on_extraction_failure(self):
        m = _m(gen=_gen(extraction_status="failed", has_extracted_code=False))
        assert m["is_full_process_reliability_metric"] is False

    def test_false_on_missing_fields(self):
        m = compute_minimal_process_metrics_from_sections({}, {})
        assert m["is_full_process_reliability_metric"] is False

    def test_false_on_timeout(self):
        m = _m(exc=_exec(execution_performed=True, tests_passed=False,
                          error_type="timeout", timed_out=True))
        assert m["is_full_process_reliability_metric"] is False


# ── 11. No LLM/Docker/retry/memory imports or calls ──────────────────────────

class TestNoForbiddenDependencies:
    def test_no_forbidden_imports(self):
        import reliability_harness.metrics.process_metrics as mod
        with open(mod.__file__, encoding="utf-8") as f:
            content = f.read()
        forbidden = [
            "LLMClient",
            "docker_runner",
            "execute_in_docker",
            "retry_controller",
            "from reliability_harness.memory",
            "from reliability_harness.runtime.agent",
            "subprocess",
        ]
        for item in forbidden:
            assert item not in content, f"Forbidden dependency found in process_metrics.py: {item!r}"
