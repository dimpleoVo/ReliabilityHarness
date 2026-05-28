"""Tests for Benchmark-5B — minimal observable failure diagnostics.

No LLM calls. No Docker. No memory/retry.

Covered:
1.  all success -> failure_observed false, failure_stage none, failure_type none
2.  extraction_status failed -> failure_stage extraction, failure_type extraction_failed
3.  has_extracted_code false -> failure_stage extraction, failure_type no_extracted_code
4.  execution_performed false -> failure_stage execution, failure_type execution_not_performed
5.  timeout -> failure_stage execution, failure_type timeout
6.  assertion_failure -> failure_type assertion_failure
7.  syntax_error -> failure_type syntax_error
8.  runtime_error -> failure_type runtime_error
9.  tests_passed false with error_type None -> unknown_execution_error
10. missing required fields -> failure_stage unknown, failure_type unknown
11. is_full_failure_taxonomy is False
12. failure_source is correctly assigned for main cases
13. no LLM / Docker / retry / memory imports or calls
"""
from __future__ import annotations

from reliability_harness.diagnostics.failure_diagnostics import (
    compute_minimal_failure_diagnostics,
    compute_minimal_failure_diagnostics_from_sections,
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


def _d(gen=None, exc=None) -> dict:
    g = gen if gen is not None else _gen()
    e = exc if exc is not None else _exec()
    return compute_minimal_failure_diagnostics_from_sections(g, e)


# ── 1. All success → failure_observed false, failure_stage none, failure_type none ──

class TestAllSuccess:
    def test_failure_observed_false(self):
        assert _d()["failure_observed"] is False

    def test_failure_stage_none(self):
        assert _d()["failure_stage"] == "none"

    def test_failure_type_none(self):
        assert _d()["failure_type"] == "none"

    def test_failure_source_null(self):
        assert _d()["failure_source"] is None

    def test_timed_out_false(self):
        assert _d()["timed_out"] is False

    def test_error_type_null(self):
        assert _d()["error_type"] is None


# ── 2. extraction_status failed → extraction stage ────────────────────────────

class TestExtractionFailed:
    def _diag(self):
        return _d(gen=_gen(extraction_status="failed", has_extracted_code=False))

    def test_failure_observed_true(self):
        assert self._diag()["failure_observed"] is True

    def test_failure_stage_extraction(self):
        assert self._diag()["failure_stage"] == "extraction"

    def test_failure_type_extraction_failed(self):
        assert self._diag()["failure_type"] == "extraction_failed"

    def test_failure_source(self):
        assert self._diag()["failure_source"] == "generation.extraction_status"


# ── 3. has_extracted_code false → extraction stage ───────────────────────────

class TestHasExtractedCodeFalse:
    def _diag(self):
        return _d(gen=_gen(extraction_status="success", has_extracted_code=False))

    def test_failure_observed_true(self):
        assert self._diag()["failure_observed"] is True

    def test_failure_stage_extraction(self):
        assert self._diag()["failure_stage"] == "extraction"

    def test_failure_type_no_extracted_code(self):
        assert self._diag()["failure_type"] == "no_extracted_code"

    def test_failure_source(self):
        assert self._diag()["failure_source"] == "generation.has_extracted_code"


# ── 4. execution_performed false → execution_not_performed ───────────────────

class TestExecutionNotPerformed:
    def _diag(self):
        return _d(exc=_exec(execution_performed=False, tests_passed=False))

    def test_failure_observed_true(self):
        assert self._diag()["failure_observed"] is True

    def test_failure_stage_execution(self):
        assert self._diag()["failure_stage"] == "execution"

    def test_failure_type_execution_not_performed(self):
        assert self._diag()["failure_type"] == "execution_not_performed"

    def test_failure_source(self):
        assert self._diag()["failure_source"] == "execution.execution_performed"


# ── 5. timeout ────────────────────────────────────────────────────────────────

class TestTimeout:
    def _diag(self):
        return _d(exc=_exec(
            execution_performed=True,
            tests_passed=False,
            error_type="timeout",
            timed_out=True,
        ))

    def test_failure_observed_true(self):
        assert self._diag()["failure_observed"] is True

    def test_failure_stage_execution(self):
        assert self._diag()["failure_stage"] == "execution"

    def test_failure_type_timeout(self):
        assert self._diag()["failure_type"] == "timeout"

    def test_timed_out_true(self):
        assert self._diag()["timed_out"] is True

    def test_failure_source(self):
        assert self._diag()["failure_source"] == "execution.timed_out"


# ── 6. assertion_failure ──────────────────────────────────────────────────────

class TestAssertionFailure:
    def _diag(self):
        return _d(exc=_exec(
            execution_performed=True,
            tests_passed=False,
            error_type="assertion_failure",
            timed_out=False,
        ))

    def test_failure_observed_true(self):
        assert self._diag()["failure_observed"] is True

    def test_failure_stage_execution(self):
        assert self._diag()["failure_stage"] == "execution"

    def test_failure_type_assertion_failure(self):
        assert self._diag()["failure_type"] == "assertion_failure"

    def test_failure_source(self):
        assert self._diag()["failure_source"] == "execution.error_type"


# ── 7. syntax_error ───────────────────────────────────────────────────────────

class TestSyntaxError:
    def _diag(self):
        return _d(exc=_exec(
            execution_performed=True,
            tests_passed=False,
            error_type="syntax_error",
            timed_out=False,
        ))

    def test_failure_type_syntax_error(self):
        assert self._diag()["failure_type"] == "syntax_error"

    def test_failure_stage_execution(self):
        assert self._diag()["failure_stage"] == "execution"

    def test_failure_source(self):
        assert self._diag()["failure_source"] == "execution.error_type"


# ── 8. runtime_error ──────────────────────────────────────────────────────────

class TestRuntimeError:
    def _diag(self):
        return _d(exc=_exec(
            execution_performed=True,
            tests_passed=False,
            error_type="runtime_error",
            timed_out=False,
        ))

    def test_failure_type_runtime_error(self):
        assert self._diag()["failure_type"] == "runtime_error"

    def test_failure_stage_execution(self):
        assert self._diag()["failure_stage"] == "execution"

    def test_failure_source(self):
        assert self._diag()["failure_source"] == "execution.error_type"


# ── 9. tests_passed False with error_type None → unknown_execution_error ──────

class TestUnknownExecutionError:
    def _diag(self):
        return _d(exc=_exec(
            execution_performed=True,
            tests_passed=False,
            error_type=None,
            timed_out=False,
        ))

    def test_failure_observed_true(self):
        assert self._diag()["failure_observed"] is True

    def test_failure_stage_execution(self):
        assert self._diag()["failure_stage"] == "execution"

    def test_failure_type_unknown_execution_error(self):
        assert self._diag()["failure_type"] == "unknown_execution_error"

    def test_failure_source(self):
        assert self._diag()["failure_source"] == "execution.tests_passed"


# ── 10. Missing required fields → failure_stage unknown, failure_type unknown ─

class TestMissingFields:
    def test_empty_dicts_give_unknown_stage(self):
        d = compute_minimal_failure_diagnostics_from_sections({}, {})
        assert d["failure_stage"] == "unknown"

    def test_empty_dicts_give_unknown_type(self):
        d = compute_minimal_failure_diagnostics_from_sections({}, {})
        assert d["failure_type"] == "unknown"

    def test_none_sections_give_unknown(self):
        d = compute_minimal_failure_diagnostics({"generation": None, "execution": None})
        assert d["failure_stage"] == "unknown"

    def test_missing_summary_sections_give_unknown(self):
        d = compute_minimal_failure_diagnostics({})
        assert d["failure_stage"] == "unknown"

    def test_non_dict_input_gives_unknown(self):
        d = compute_minimal_failure_diagnostics_from_sections("bad", 42)
        assert d["failure_stage"] == "unknown"

    def test_missing_extraction_status_gives_unknown(self):
        d = compute_minimal_failure_diagnostics_from_sections(
            {"has_extracted_code": True}, _exec()
        )
        assert d["failure_stage"] == "unknown"

    def test_non_dict_summary_gives_unknown(self):
        d = compute_minimal_failure_diagnostics("not a dict")
        assert d["failure_stage"] == "unknown"


# ── 11. is_full_failure_taxonomy is always False ──────────────────────────────

class TestIsFullFailureTaxonomy:
    def test_false_on_success(self):
        assert _d()["is_full_failure_taxonomy"] is False

    def test_false_on_extraction_failure(self):
        d = _d(gen=_gen(extraction_status="failed", has_extracted_code=False))
        assert d["is_full_failure_taxonomy"] is False

    def test_false_on_timeout(self):
        d = _d(exc=_exec(execution_performed=True, tests_passed=False,
                          error_type="timeout", timed_out=True))
        assert d["is_full_failure_taxonomy"] is False

    def test_false_on_missing_fields(self):
        d = compute_minimal_failure_diagnostics_from_sections({}, {})
        assert d["is_full_failure_taxonomy"] is False


# ── 12. Fixed field set ───────────────────────────────────────────────────────

class TestFixedFieldSet:
    _EXPECTED_KEYS = {
        "failure_observed",
        "failure_stage",
        "failure_type",
        "failure_source",
        "timed_out",
        "error_type",
        "is_full_failure_taxonomy",
        "definition",
    }

    def test_all_expected_keys_present_success(self):
        assert set(_d().keys()) == self._EXPECTED_KEYS

    def test_all_expected_keys_present_unknown(self):
        d = compute_minimal_failure_diagnostics_from_sections({}, {})
        assert set(d.keys()) == self._EXPECTED_KEYS

    def test_definition_is_nonempty_string(self):
        assert isinstance(_d()["definition"], str)
        assert len(_d()["definition"]) > 0

    def test_failure_stage_valid_enum(self):
        valid = {"none", "extraction", "execution", "unknown"}
        assert _d()["failure_stage"] in valid

    def test_failure_stage_unknown_in_valid_enum(self):
        valid = {"none", "extraction", "execution", "unknown"}
        d = compute_minimal_failure_diagnostics_from_sections({}, {})
        assert d["failure_stage"] in valid


# ── 13. No LLM / Docker / retry / memory imports or calls ────────────────────

class TestNoForbiddenDependencies:
    def test_no_forbidden_imports(self):
        import reliability_harness.diagnostics.failure_diagnostics as mod
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
            assert item not in content, (
                f"Forbidden dependency found in failure_diagnostics.py: {item!r}"
            )
