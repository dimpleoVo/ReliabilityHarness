"""Tests for Benchmark-6A — aggregate summary over run summaries.

No LLM calls. No Docker. No memory/retry. No code execution.

Covered:
1.  empty run summaries -> total_runs 0, rates 0.0
2.  single successful run -> counts/rates correct
3.  multiple mixed runs -> counts/rates correct
4.  failure_stage_distribution counts none/extraction/execution/unknown
5.  failure_type_distribution counts none/timeout/runtime_error/assertion_failure
6.  timeout_count uses metrics.process.timeout_observed
7.  runtime_error_count uses metrics.process.runtime_error_observed
8.  failure_observed_count uses diagnostics.failure.failure_observed
9.  final_success_rate uses success.final_success, not observable_process_success
10. observable_process_success_rate uses metrics.process.observable_process_success
11. missing required fields raises AggregateSummaryError
12. no secrets in aggregate summary values
13. aggregate summary does not copy prompt/raw_response/extracted_code/candidate_code/stdout/stderr
14. write_aggregate_summary writes to tmp_path
15. build_aggregate_summary_from_paths loads summaries from paths
16. no LLM/Docker/retry/memory imports or calls
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from reliability_harness.artifacts.aggregate_summary import (
    AggregateSummaryError,
    build_aggregate_summary,
    build_aggregate_summary_from_paths,
    load_json,
    write_aggregate_summary,
)


# ── Fixtures ───────────────────────────────────────────────────────────────────

def _run_summary(
    *,
    final_success: bool = True,
    observable_process_success: bool = True,
    timeout_observed: bool = False,
    runtime_error_observed: bool = False,
    failure_observed: bool = False,
    failure_stage: str = "none",
    failure_type: str = "none",
) -> dict:
    """Minimal run summary dict with all required fields."""
    return {
        "artifact_version": "4D.1",
        "success": {
            "final_success": final_success,
            "definition": "...",
            "is_process_reliability_metric": False,
        },
        "metrics": {
            "process": {
                "observable_process_success": observable_process_success,
                "timeout_observed": timeout_observed,
                "runtime_error_observed": runtime_error_observed,
                "is_full_process_reliability_metric": False,
            },
            "recovery": {},
            "memory": {},
        },
        "diagnostics": {
            "failure": {
                "failure_observed": failure_observed,
                "failure_stage": failure_stage,
                "failure_type": failure_type,
                "is_full_failure_taxonomy": False,
            },
        },
    }


def _success_summary() -> dict:
    return _run_summary(
        final_success=True,
        observable_process_success=True,
        timeout_observed=False,
        runtime_error_observed=False,
        failure_observed=False,
        failure_stage="none",
        failure_type="none",
    )


def _timeout_summary() -> dict:
    return _run_summary(
        final_success=False,
        observable_process_success=False,
        timeout_observed=True,
        runtime_error_observed=False,
        failure_observed=True,
        failure_stage="execution",
        failure_type="timeout",
    )


def _runtime_error_summary() -> dict:
    return _run_summary(
        final_success=False,
        observable_process_success=False,
        timeout_observed=False,
        runtime_error_observed=True,
        failure_observed=True,
        failure_stage="execution",
        failure_type="runtime_error",
    )


def _extraction_failure_summary() -> dict:
    return _run_summary(
        final_success=False,
        observable_process_success=False,
        timeout_observed=False,
        runtime_error_observed=False,
        failure_observed=True,
        failure_stage="extraction",
        failure_type="extraction_failed",
    )


def _assertion_failure_summary() -> dict:
    return _run_summary(
        final_success=False,
        observable_process_success=False,
        timeout_observed=False,
        runtime_error_observed=False,
        failure_observed=True,
        failure_stage="execution",
        failure_type="assertion_failure",
    )


# ── 1. Empty run summaries ─────────────────────────────────────────────────────

class TestEmptyRunSummaries:
    def test_total_runs_zero(self):
        agg = build_aggregate_summary([])
        assert agg["counts"]["total_runs"] == 0

    def test_all_counts_zero(self):
        agg = build_aggregate_summary([])
        counts = agg["counts"]
        assert counts["final_success_count"] == 0
        assert counts["observable_process_success_count"] == 0
        assert counts["failure_observed_count"] == 0
        assert counts["timeout_count"] == 0
        assert counts["runtime_error_count"] == 0

    def test_all_rates_zero(self):
        agg = build_aggregate_summary([])
        rates = agg["rates"]
        for key, val in rates.items():
            assert val == 0.0, f"Expected 0.0 for {key!r}, got {val}"

    def test_distributions_empty(self):
        agg = build_aggregate_summary([])
        assert agg["distributions"]["failure_stage_distribution"] == {}
        assert agg["distributions"]["failure_type_distribution"] == {}

    def test_artifact_version(self):
        agg = build_aggregate_summary([])
        assert agg["artifact_version"] == "6A.1"

    def test_created_at_present(self):
        agg = build_aggregate_summary([])
        assert "created_at" in agg and agg["created_at"]


# ── 2. Single successful run ───────────────────────────────────────────────────

class TestSingleSuccessfulRun:
    def setup_method(self):
        self.agg = build_aggregate_summary([_success_summary()])

    def test_total_runs_one(self):
        assert self.agg["counts"]["total_runs"] == 1

    def test_final_success_count_one(self):
        assert self.agg["counts"]["final_success_count"] == 1

    def test_observable_process_success_count_one(self):
        assert self.agg["counts"]["observable_process_success_count"] == 1

    def test_failure_observed_count_zero(self):
        assert self.agg["counts"]["failure_observed_count"] == 0

    def test_timeout_count_zero(self):
        assert self.agg["counts"]["timeout_count"] == 0

    def test_runtime_error_count_zero(self):
        assert self.agg["counts"]["runtime_error_count"] == 0

    def test_final_success_rate_one(self):
        assert self.agg["rates"]["final_success_rate"] == 1.0

    def test_observable_process_success_rate_one(self):
        assert self.agg["rates"]["observable_process_success_rate"] == 1.0

    def test_failure_observed_rate_zero(self):
        assert self.agg["rates"]["failure_observed_rate"] == 0.0

    def test_failure_stage_none_in_distribution(self):
        dist = self.agg["distributions"]["failure_stage_distribution"]
        assert dist.get("none", 0) == 1

    def test_failure_type_none_in_distribution(self):
        dist = self.agg["distributions"]["failure_type_distribution"]
        assert dist.get("none", 0) == 1


# ── 3. Multiple mixed runs ─────────────────────────────────────────────────────

class TestMultipleMixedRuns:
    def setup_method(self):
        # 2 success, 1 timeout, 1 runtime_error, 1 extraction_failure
        summaries = [
            _success_summary(),
            _success_summary(),
            _timeout_summary(),
            _runtime_error_summary(),
            _extraction_failure_summary(),
        ]
        self.agg = build_aggregate_summary(summaries)

    def test_total_runs(self):
        assert self.agg["counts"]["total_runs"] == 5

    def test_final_success_count(self):
        assert self.agg["counts"]["final_success_count"] == 2

    def test_observable_process_success_count(self):
        assert self.agg["counts"]["observable_process_success_count"] == 2

    def test_failure_observed_count(self):
        assert self.agg["counts"]["failure_observed_count"] == 3

    def test_timeout_count(self):
        assert self.agg["counts"]["timeout_count"] == 1

    def test_runtime_error_count(self):
        assert self.agg["counts"]["runtime_error_count"] == 1

    def test_final_success_rate(self):
        assert abs(self.agg["rates"]["final_success_rate"] - 0.4) < 1e-5

    def test_observable_process_success_rate(self):
        assert abs(self.agg["rates"]["observable_process_success_rate"] - 0.4) < 1e-5

    def test_failure_observed_rate(self):
        assert abs(self.agg["rates"]["failure_observed_rate"] - 0.6) < 1e-5

    def test_timeout_rate(self):
        assert abs(self.agg["rates"]["timeout_rate"] - 0.2) < 1e-5

    def test_runtime_error_rate(self):
        assert abs(self.agg["rates"]["runtime_error_rate"] - 0.2) < 1e-5


# ── 4. failure_stage_distribution ─────────────────────────────────────────────

class TestFailureStageDistribution:
    def test_none_counted(self):
        summaries = [_success_summary(), _success_summary()]
        agg = build_aggregate_summary(summaries)
        assert agg["distributions"]["failure_stage_distribution"]["none"] == 2

    def test_extraction_counted(self):
        summaries = [_success_summary(), _extraction_failure_summary()]
        agg = build_aggregate_summary(summaries)
        dist = agg["distributions"]["failure_stage_distribution"]
        assert dist.get("extraction", 0) == 1

    def test_execution_counted(self):
        summaries = [_timeout_summary(), _runtime_error_summary()]
        agg = build_aggregate_summary(summaries)
        dist = agg["distributions"]["failure_stage_distribution"]
        assert dist.get("execution", 0) == 2

    def test_unknown_counted(self):
        unknown = _run_summary(
            failure_observed=True,
            failure_stage="unknown",
            failure_type="unknown",
            final_success=False,
            observable_process_success=False,
        )
        agg = build_aggregate_summary([unknown])
        assert agg["distributions"]["failure_stage_distribution"]["unknown"] == 1

    def test_mixed_distribution(self):
        summaries = [
            _success_summary(),
            _extraction_failure_summary(),
            _timeout_summary(),
        ]
        agg = build_aggregate_summary(summaries)
        dist = agg["distributions"]["failure_stage_distribution"]
        assert dist["none"] == 1
        assert dist["extraction"] == 1
        assert dist["execution"] == 1


# ── 5. failure_type_distribution ──────────────────────────────────────────────

class TestFailureTypeDistribution:
    def test_none_counted(self):
        agg = build_aggregate_summary([_success_summary()])
        assert agg["distributions"]["failure_type_distribution"]["none"] == 1

    def test_timeout_counted(self):
        agg = build_aggregate_summary([_timeout_summary()])
        assert agg["distributions"]["failure_type_distribution"]["timeout"] == 1

    def test_runtime_error_counted(self):
        agg = build_aggregate_summary([_runtime_error_summary()])
        assert agg["distributions"]["failure_type_distribution"]["runtime_error"] == 1

    def test_assertion_failure_counted(self):
        agg = build_aggregate_summary([_assertion_failure_summary()])
        assert agg["distributions"]["failure_type_distribution"]["assertion_failure"] == 1

    def test_extraction_failed_counted(self):
        agg = build_aggregate_summary([_extraction_failure_summary()])
        assert agg["distributions"]["failure_type_distribution"]["extraction_failed"] == 1

    def test_multi_type_distribution(self):
        summaries = [
            _success_summary(),
            _timeout_summary(),
            _timeout_summary(),
            _runtime_error_summary(),
        ]
        agg = build_aggregate_summary(summaries)
        dist = agg["distributions"]["failure_type_distribution"]
        assert dist["none"] == 1
        assert dist["timeout"] == 2
        assert dist["runtime_error"] == 1


# ── 6. timeout_count uses metrics.process.timeout_observed ─────────────────────

class TestTimeoutCountSource:
    def test_timeout_observed_true_increments_timeout_count(self):
        s = _run_summary(timeout_observed=True, failure_observed=True,
                         failure_stage="execution", failure_type="timeout",
                         final_success=False, observable_process_success=False)
        agg = build_aggregate_summary([s])
        assert agg["counts"]["timeout_count"] == 1

    def test_timeout_observed_false_does_not_increment(self):
        agg = build_aggregate_summary([_success_summary()])
        assert agg["counts"]["timeout_count"] == 0

    def test_timeout_count_is_independent_of_failure_type(self):
        # timeout_count from metrics.process.timeout_observed, not failure_type
        s_timeout_observed = _run_summary(
            timeout_observed=True, final_success=False,
            observable_process_success=False, failure_observed=True,
            failure_stage="execution", failure_type="assertion_failure",  # mismatch intentional
        )
        agg = build_aggregate_summary([s_timeout_observed])
        assert agg["counts"]["timeout_count"] == 1


# ── 7. runtime_error_count uses metrics.process.runtime_error_observed ─────────

class TestRuntimeErrorCountSource:
    def test_runtime_error_observed_true_increments(self):
        s = _run_summary(runtime_error_observed=True, failure_observed=True,
                         failure_stage="execution", failure_type="runtime_error",
                         final_success=False, observable_process_success=False)
        agg = build_aggregate_summary([s])
        assert agg["counts"]["runtime_error_count"] == 1

    def test_runtime_error_observed_false_does_not_increment(self):
        agg = build_aggregate_summary([_success_summary()])
        assert agg["counts"]["runtime_error_count"] == 0


# ── 8. failure_observed_count uses diagnostics.failure.failure_observed ─────────

class TestFailureObservedCountSource:
    def test_failure_observed_true_increments(self):
        s = _run_summary(failure_observed=True, failure_stage="extraction",
                         failure_type="extraction_failed", final_success=False,
                         observable_process_success=False)
        agg = build_aggregate_summary([s])
        assert agg["counts"]["failure_observed_count"] == 1

    def test_failure_observed_false_does_not_increment(self):
        agg = build_aggregate_summary([_success_summary()])
        assert agg["counts"]["failure_observed_count"] == 0


# ── 9. final_success_rate uses success.final_success ──────────────────────────

class TestFinalSuccessRateSource:
    def test_uses_success_final_success(self):
        # final_success=True but observable_process_success=False (intentional mismatch)
        s = _run_summary(final_success=True, observable_process_success=False,
                         failure_observed=False, failure_stage="none",
                         failure_type="none")
        agg = build_aggregate_summary([s])
        assert agg["counts"]["final_success_count"] == 1
        assert agg["counts"]["observable_process_success_count"] == 0
        assert agg["rates"]["final_success_rate"] == 1.0
        assert agg["rates"]["observable_process_success_rate"] == 0.0

    def test_final_success_false_not_counted(self):
        s = _run_summary(final_success=False, observable_process_success=True,
                         failure_observed=False, failure_stage="none",
                         failure_type="none")
        agg = build_aggregate_summary([s])
        assert agg["counts"]["final_success_count"] == 0
        assert agg["counts"]["observable_process_success_count"] == 1


# ── 10. observable_process_success_rate source ────────────────────────────────

class TestObservableProcessSuccessRateSource:
    def test_uses_metrics_process_field(self):
        summaries = [_success_summary(), _success_summary(), _timeout_summary()]
        agg = build_aggregate_summary(summaries)
        assert agg["counts"]["observable_process_success_count"] == 2
        assert abs(agg["rates"]["observable_process_success_rate"] - 2 / 3) < 1e-5


# ── 11. Missing required fields raises AggregateSummaryError ──────────────────

class TestMissingFieldsRaisesError:
    def test_non_list_input_raises(self):
        with pytest.raises(AggregateSummaryError, match="list"):
            build_aggregate_summary({"not": "a list"})

    def test_missing_success_section_raises(self):
        s = _run_summary()
        del s["success"]
        with pytest.raises(AggregateSummaryError):
            build_aggregate_summary([s])

    def test_missing_final_success_raises(self):
        s = _run_summary()
        del s["success"]["final_success"]
        with pytest.raises(AggregateSummaryError):
            build_aggregate_summary([s])

    def test_missing_metrics_process_raises(self):
        s = _run_summary()
        del s["metrics"]["process"]
        with pytest.raises(AggregateSummaryError):
            build_aggregate_summary([s])

    def test_missing_observable_process_success_raises(self):
        s = _run_summary()
        del s["metrics"]["process"]["observable_process_success"]
        with pytest.raises(AggregateSummaryError):
            build_aggregate_summary([s])

    def test_missing_timeout_observed_raises(self):
        s = _run_summary()
        del s["metrics"]["process"]["timeout_observed"]
        with pytest.raises(AggregateSummaryError):
            build_aggregate_summary([s])

    def test_missing_runtime_error_observed_raises(self):
        s = _run_summary()
        del s["metrics"]["process"]["runtime_error_observed"]
        with pytest.raises(AggregateSummaryError):
            build_aggregate_summary([s])

    def test_missing_diagnostics_failure_raises(self):
        s = _run_summary()
        del s["diagnostics"]["failure"]
        with pytest.raises(AggregateSummaryError):
            build_aggregate_summary([s])

    def test_missing_failure_observed_raises(self):
        s = _run_summary()
        del s["diagnostics"]["failure"]["failure_observed"]
        with pytest.raises(AggregateSummaryError):
            build_aggregate_summary([s])

    def test_missing_failure_stage_raises(self):
        s = _run_summary()
        del s["diagnostics"]["failure"]["failure_stage"]
        with pytest.raises(AggregateSummaryError):
            build_aggregate_summary([s])

    def test_missing_failure_type_raises(self):
        s = _run_summary()
        del s["diagnostics"]["failure"]["failure_type"]
        with pytest.raises(AggregateSummaryError):
            build_aggregate_summary([s])

    def test_non_dict_summary_raises(self):
        with pytest.raises(AggregateSummaryError):
            build_aggregate_summary(["not a dict"])

    def test_error_mentions_index(self):
        # second summary is broken; error should mention index 1
        bad = _run_summary()
        del bad["success"]["final_success"]
        with pytest.raises(AggregateSummaryError, match="1"):
            build_aggregate_summary([_success_summary(), bad])


# ── 12. No secrets in aggregate summary values ────────────────────────────────

class TestNoSecretsInSummary:
    _FORBIDDEN = ["DEEPSEEK_API_KEY", "deepseek_api_key", "api_key=", "sk-", ".env"]

    def test_no_secrets_in_serialized_summary(self):
        agg = build_aggregate_summary([_success_summary()])
        text = json.dumps(agg)
        for pattern in self._FORBIDDEN:
            assert pattern not in text, f"Forbidden pattern {pattern!r} in aggregate JSON"


# ── 13. No large raw fields copied ────────────────────────────────────────────

class TestNoRawFieldsCopied:
    _FORBIDDEN_KEYS = ("prompt", "raw_response", "extracted_code",
                       "candidate_code", "stdout", "stderr")

    def test_no_forbidden_keys_in_aggregate(self):
        # Add forbidden keys into source summaries — they must not appear in output
        s = _run_summary()
        s["prompt"] = "secret prompt"
        s["raw_response"] = "secret response"
        s["extracted_code"] = "def f(): pass"
        agg = build_aggregate_summary([s])
        text = json.dumps(agg)
        for key in self._FORBIDDEN_KEYS:
            assert f'"{key}"' not in text, (
                f"Forbidden key {key!r} found in aggregate summary JSON"
            )


# ── 14. write_aggregate_summary writes to tmp_path ────────────────────────────

class TestWriteAggregateSummary:
    def test_write_creates_file(self, tmp_path):
        agg = build_aggregate_summary([_success_summary()])
        path = write_aggregate_summary(agg, output_dir=tmp_path)
        assert path.exists()

    def test_written_file_is_valid_json(self, tmp_path):
        agg = build_aggregate_summary([_success_summary()])
        path = write_aggregate_summary(agg, output_dir=tmp_path)
        with open(path, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded["artifact_version"] == "6A.1"

    def test_written_file_roundtrip(self, tmp_path):
        agg = build_aggregate_summary([_success_summary(), _timeout_summary()])
        path = write_aggregate_summary(agg, output_dir=tmp_path)
        with open(path, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded["counts"]["total_runs"] == 2

    def test_write_returns_path_object(self, tmp_path):
        agg = build_aggregate_summary([])
        path = write_aggregate_summary(agg, output_dir=tmp_path)
        assert isinstance(path, Path)

    def test_write_filename_prefix(self, tmp_path):
        agg = build_aggregate_summary([])
        path = write_aggregate_summary(agg, output_dir=tmp_path)
        assert path.name.startswith("aggregate_summary_")
        assert path.name.endswith(".json")

    def test_default_output_dir(self, monkeypatch, tmp_path):
        import reliability_harness.artifacts.aggregate_summary as agg_mod
        monkeypatch.setattr(agg_mod, "_AGGREGATE_SUMMARIES_ROOT", tmp_path / "agg")
        agg = build_aggregate_summary([])
        path = write_aggregate_summary(agg)
        assert (tmp_path / "agg").is_dir()
        assert path.parent == (tmp_path / "agg")


# ── 15. build_aggregate_summary_from_paths ────────────────────────────────────

class TestBuildFromPaths:
    def test_loads_and_aggregates(self, tmp_path):
        s1 = _success_summary()
        s2 = _timeout_summary()
        p1 = tmp_path / "s1.json"
        p2 = tmp_path / "s2.json"
        p1.write_text(json.dumps(s1), encoding="utf-8")
        p2.write_text(json.dumps(s2), encoding="utf-8")
        agg = build_aggregate_summary_from_paths([p1, p2])
        assert agg["counts"]["total_runs"] == 2
        assert agg["counts"]["final_success_count"] == 1

    def test_paths_stored_in_input(self, tmp_path):
        s = _success_summary()
        p = tmp_path / "s.json"
        p.write_text(json.dumps(s), encoding="utf-8")
        agg = build_aggregate_summary_from_paths([p])
        assert str(p) in agg["input"]["run_summary_paths"]

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(AggregateSummaryError, match="not found"):
            build_aggregate_summary_from_paths([tmp_path / "missing.json"])

    def test_invalid_json_raises(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("not json {{{", encoding="utf-8")
        with pytest.raises(AggregateSummaryError, match="not valid JSON"):
            build_aggregate_summary_from_paths([p])

    def test_empty_paths_list(self):
        agg = build_aggregate_summary_from_paths([])
        assert agg["counts"]["total_runs"] == 0


# ── top-level schema keys ──────────────────────────────────────────────────────

class TestTopLevelSchema:
    _REQUIRED = ("artifact_version", "created_at", "input", "counts",
                 "rates", "distributions", "limitations")

    def test_all_top_level_keys_present(self):
        agg = build_aggregate_summary([_success_summary()])
        for key in self._REQUIRED:
            assert key in agg, f"Missing top-level key: {key!r}"

    def test_counts_keys(self):
        agg = build_aggregate_summary([])
        expected = {"total_runs", "final_success_count", "observable_process_success_count",
                    "failure_observed_count", "timeout_count", "runtime_error_count"}
        assert set(agg["counts"].keys()) == expected

    def test_rates_keys(self):
        agg = build_aggregate_summary([])
        expected = {"final_success_rate", "observable_process_success_rate",
                    "failure_observed_rate", "timeout_rate", "runtime_error_rate"}
        assert set(agg["rates"].keys()) == expected

    def test_distributions_keys(self):
        agg = build_aggregate_summary([])
        expected = {"failure_stage_distribution", "failure_type_distribution"}
        assert set(agg["distributions"].keys()) == expected

    def test_limitations_is_nonempty_list(self):
        agg = build_aggregate_summary([])
        assert isinstance(agg["limitations"], list)
        assert len(agg["limitations"]) > 0

    def test_limitations_mention_not_reliability_score(self):
        agg = build_aggregate_summary([])
        combined = " ".join(agg["limitations"]).lower()
        assert "not a full reliability score" in combined or "not a full" in combined

    def test_run_summary_paths_in_input(self):
        agg = build_aggregate_summary(
            [_success_summary()],
            run_summary_paths=["path/to/s1.json"],
        )
        assert "path/to/s1.json" in agg["input"]["run_summary_paths"]


# ── load_json helper ───────────────────────────────────────────────────────────

class TestLoadJson:
    def test_load_valid_json(self, tmp_path):
        p = tmp_path / "f.json"
        p.write_text('{"key": "value"}', encoding="utf-8")
        assert load_json(p) == {"key": "value"}

    def test_load_missing_raises(self, tmp_path):
        with pytest.raises(AggregateSummaryError, match="not found"):
            load_json(tmp_path / "missing.json")

    def test_load_invalid_json_raises(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("not json", encoding="utf-8")
        with pytest.raises(AggregateSummaryError, match="not valid JSON"):
            load_json(p)


# ── 16. No LLM/Docker/retry/memory imports or calls ──────────────────────────

class TestNoForbiddenDependencies:
    def test_no_forbidden_imports(self):
        import reliability_harness.artifacts.aggregate_summary as mod
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
                f"Forbidden dependency found in aggregate_summary.py: {item!r}"
            )
