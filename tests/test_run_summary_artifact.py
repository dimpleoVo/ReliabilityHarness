"""Tests for Benchmark-4D.1 — run summary artifact builder.
Benchmark-5A — metrics.process auto-populated.
Benchmark-5B — diagnostics.failure auto-populated.

No LLM calls. No Docker. No memory/retry. No real execution.

Covered:
1.  Valid generation + execution artifacts -> summary dict is returned
2.  Summary top-level contains all required envelope keys
3.  identity contains run_id / benchmark / task_id / model_name
4.  artifact_refs preserves generation_artifact_path / execution_artifact_path
5.  extraction_status success + execution_performed + tests_passed -> final_success True
6.  extraction_status not "success" -> final_success False
7.  tests_passed False -> final_success False
8.  execution_performed False -> final_success False
9.  timed_out is included in execution section
10. error_type is included in execution section
11. model_name is preserved in identity
12. metrics has process (populated) / recovery {} / memory {}
13. diagnostics has failure (populated, not empty dict)
14. success.is_process_reliability_metric is False
15. limitations mentions final_success not a process reliability metric
16. summary does NOT copy prompt/raw_response/extracted_code/candidate_code/stdout/stderr
17. No secrets in summary (DEEPSEEK_API_KEY, api_key=, sk-, .env)
18. Missing required generation fields raises RunSummaryError
19. Mismatched benchmark/task_id raises RunSummaryError
20. write_run_summary writes to tmp_path
21. write_run_summary default path uses ARTIFACTS_ROOT / run_summaries
22. sanitized filename handles task_id with slash (HumanEval/0 -> HumanEval_0)
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from reliability_harness.artifacts.run_summary import (
    RunSummaryError,
    build_run_summary,
    build_run_summary_from_paths,
    load_json,
    write_run_summary,
)


# ── Fixtures ───────────────────────────────────────────────────────────────────

def _gen_artifact(
    *,
    run_id: str = "run_test_001",
    benchmark: str = "tiny",
    task_id: str = "tiny_0",
    model_name: str = "mock-model",
    extraction_status: str = "success",
    extracted_code: str = "def solve(): return 42",
) -> dict:
    return {
        "run_id": run_id,
        "benchmark": benchmark,
        "task_id": task_id,
        "model_name": model_name,
        "prompt": "Write a function that returns 42.",
        "raw_response": "```python\ndef solve(): return 42\n```",
        "extracted_code": extracted_code,
        "extraction_status": extraction_status,
        "error": None,
        "timestamp": "2026-01-01T00:00:00+00:00",
        "llm_used": True,
        "docker_used": False,
        "execution_performed": False,
    }


def _exec_artifact(
    *,
    run_id: str = "run_test_001",
    benchmark: str = "tiny",
    task_id: str = "tiny_0",
    execution_performed: bool = True,
    tests_passed: bool = True,
    docker_used: bool = True,
    error_type: str | None = None,
    timed_out: bool = False,
    execution_time_ms: int = 250,
) -> dict:
    return {
        "artifact_version": "4A.1",
        "created_at": "2026-01-01T00:00:00+00:00",
        "run_id": run_id,
        "benchmark": benchmark,
        "task_id": task_id,
        "candidate_code": "def solve(): return 42",
        "tests": ["assert solve() == 42"],
        "source_generation_artifact": None,
        "result": {
            "exit_code": 0,
            "stdout": "",
            "stderr": "",
            "timed_out": timed_out,
            "tests_passed": tests_passed,
            "error_type": error_type,
            "execution_time_ms": execution_time_ms,
            "docker_used": docker_used,
            "execution_performed": execution_performed,
        },
    }


def _build(gen_override=None, exec_override=None, gen_path="gen.json", exec_path="exec.json"):
    gen = gen_override if gen_override is not None else _gen_artifact()
    exec_ = exec_override if exec_override is not None else _exec_artifact()
    return build_run_summary(
        gen,
        exec_,
        generation_artifact_path=gen_path,
        execution_artifact_path=exec_path,
    )


# ── 1. Valid artifacts -> summary returned ─────────────────────────────────────

class TestBasicSummaryBuilt:
    def test_returns_dict(self):
        result = _build()
        assert isinstance(result, dict)

    def test_artifact_version(self):
        result = _build()
        assert result["artifact_version"] == "4D.1"

    def test_created_at_present(self):
        result = _build()
        assert "created_at" in result
        assert result["created_at"]


# ── 2. Top-level envelope keys ─────────────────────────────────────────────────

class TestTopLevelKeys:
    _REQUIRED = (
        "artifact_version",
        "created_at",
        "identity",
        "artifact_refs",
        "generation",
        "execution",
        "success",
        "metrics",
        "diagnostics",
        "limitations",
    )

    def test_all_top_level_keys_present(self):
        result = _build()
        for key in self._REQUIRED:
            assert key in result, f"Missing top-level key: {key!r}"


# ── 3. identity ────────────────────────────────────────────────────────────────

class TestIdentitySection:
    def test_run_id(self):
        result = _build()
        assert result["identity"]["run_id"] == "run_test_001"

    def test_benchmark(self):
        result = _build()
        assert result["identity"]["benchmark"] == "tiny"

    def test_task_id(self):
        result = _build()
        assert result["identity"]["task_id"] == "tiny_0"

    def test_model_name(self):
        result = _build()
        assert result["identity"]["model_name"] == "mock-model"


# ── 4. artifact_refs ───────────────────────────────────────────────────────────

class TestArtifactRefs:
    def test_generation_artifact_path_preserved(self):
        result = _build(gen_path="/some/path/gen.json")
        assert result["artifact_refs"]["generation_artifact_path"] == "/some/path/gen.json"

    def test_execution_artifact_path_preserved(self):
        result = _build(exec_path="/some/path/exec.json")
        assert result["artifact_refs"]["execution_artifact_path"] == "/some/path/exec.json"


# ── 5–8. final_success logic ───────────────────────────────────────────────────

class TestFinalSuccess:
    def test_all_conditions_true_gives_final_success_true(self):
        result = _build(
            _gen_artifact(extraction_status="success"),
            _exec_artifact(execution_performed=True, tests_passed=True),
        )
        assert result["success"]["final_success"] is True

    def test_extraction_status_failed_gives_final_success_false(self):
        result = _build(
            _gen_artifact(extraction_status="failed"),
            _exec_artifact(execution_performed=True, tests_passed=True),
        )
        assert result["success"]["final_success"] is False

    def test_extraction_status_empty_gives_final_success_false(self):
        result = _build(
            _gen_artifact(extraction_status=""),
            _exec_artifact(execution_performed=True, tests_passed=True),
        )
        assert result["success"]["final_success"] is False

    def test_tests_passed_false_gives_final_success_false(self):
        result = _build(
            _gen_artifact(extraction_status="success"),
            _exec_artifact(execution_performed=True, tests_passed=False),
        )
        assert result["success"]["final_success"] is False

    def test_execution_performed_false_gives_final_success_false(self):
        result = _build(
            _gen_artifact(extraction_status="success"),
            _exec_artifact(execution_performed=False, tests_passed=True),
        )
        assert result["success"]["final_success"] is False

    def test_all_conditions_false_gives_final_success_false(self):
        result = _build(
            _gen_artifact(extraction_status="failed"),
            _exec_artifact(execution_performed=False, tests_passed=False),
        )
        assert result["success"]["final_success"] is False


# ── 9. timed_out in execution section ─────────────────────────────────────────

class TestTimedOut:
    def test_timed_out_false_included(self):
        result = _build(exec_override=_exec_artifact(timed_out=False))
        assert result["execution"]["timed_out"] is False

    def test_timed_out_true_included(self):
        result = _build(exec_override=_exec_artifact(timed_out=True))
        assert result["execution"]["timed_out"] is True


# ── 10. error_type in execution section ───────────────────────────────────────

class TestErrorType:
    def test_error_type_none_included(self):
        result = _build(exec_override=_exec_artifact(error_type=None))
        assert result["execution"]["error_type"] is None

    def test_error_type_assertion_failure_included(self):
        result = _build(exec_override=_exec_artifact(error_type="assertion_failure"))
        assert result["execution"]["error_type"] == "assertion_failure"

    def test_error_type_timeout_included(self):
        result = _build(exec_override=_exec_artifact(error_type="timeout", timed_out=True))
        assert result["execution"]["error_type"] == "timeout"


# ── 11. model_name preserved ───────────────────────────────────────────────────

class TestModelNamePreserved:
    def test_custom_model_name_in_identity(self):
        gen = _gen_artifact(model_name="deepseek-chat")
        result = _build(gen_override=gen)
        assert result["identity"]["model_name"] == "deepseek-chat"


# ── 12. metrics extension points ─────────────────────────────────────────────

class TestMetricsExtensionPoints:
    def test_metrics_process_is_populated_dict(self):
        result = _build()
        assert isinstance(result["metrics"]["process"], dict)
        assert len(result["metrics"]["process"]) > 0

    def test_metrics_recovery_is_empty_dict(self):
        result = _build()
        assert result["metrics"]["recovery"] == {}

    def test_metrics_memory_is_empty_dict(self):
        result = _build()
        assert result["metrics"]["memory"] == {}

    def test_metrics_has_exactly_three_keys(self):
        result = _build()
        assert set(result["metrics"].keys()) == {"process", "recovery", "memory"}


# ── 13. diagnostics.failure is populated (Benchmark-5B) ──────────────────────

class TestDiagnosticsExtensionPoint:
    def test_diagnostics_failure_is_populated_dict(self):
        result = _build()
        assert isinstance(result["diagnostics"]["failure"], dict)
        assert len(result["diagnostics"]["failure"]) > 0

    def test_diagnostics_failure_has_failure_observed(self):
        result = _build()
        assert "failure_observed" in result["diagnostics"]["failure"]

    def test_diagnostics_failure_has_failure_stage(self):
        result = _build()
        assert "failure_stage" in result["diagnostics"]["failure"]


# ── 14. success.is_process_reliability_metric is False ───────────────────────

class TestIsProcessReliabilityMetric:
    def test_is_process_reliability_metric_false(self):
        result = _build()
        assert result["success"]["is_process_reliability_metric"] is False


# ── 15. limitations mention final_success proxy ───────────────────────────────

class TestLimitations:
    def test_limitations_is_list(self):
        result = _build()
        assert isinstance(result["limitations"], list)
        assert len(result["limitations"]) > 0

    def test_limitations_mention_final_success_proxy(self):
        result = _build()
        combined = " ".join(result["limitations"]).lower()
        assert "final_success" in combined or "final success" in combined

    def test_limitations_mention_process_reliability(self):
        result = _build()
        combined = " ".join(result["limitations"]).lower()
        assert "process reliability" in combined or "process_reliability" in combined

    def test_limitations_mention_4d1(self):
        result = _build()
        combined = " ".join(result["limitations"])
        assert "4D.1" in combined


# ── 16. summary does NOT copy large raw fields ───────────────────────────────

class TestNoCopyOfRawFields:
    _FORBIDDEN_KEYS = (
        "prompt",
        "raw_response",
        "extracted_code",
        "candidate_code",
        "stdout",
        "stderr",
    )

    def test_no_forbidden_keys_at_top_level(self):
        result = _build()
        for key in self._FORBIDDEN_KEYS:
            assert key not in result, f"Forbidden key {key!r} present at top level"

    def test_no_forbidden_keys_in_generation_section(self):
        result = _build()
        gen_section = result["generation"]
        for key in self._FORBIDDEN_KEYS:
            assert key not in gen_section, (
                f"Forbidden key {key!r} present in generation section"
            )

    def test_no_forbidden_keys_in_execution_section(self):
        result = _build()
        exec_section = result["execution"]
        for key in self._FORBIDDEN_KEYS:
            assert key not in exec_section, (
                f"Forbidden key {key!r} present in execution section"
            )


# ── 17. No secrets in summary values ─────────────────────────────────────────

class TestNoSecretsInSummary:
    _FORBIDDEN_PATTERNS = ["DEEPSEEK_API_KEY", "deepseek_api_key", "api_key=", "sk-", ".env"]

    def test_no_secrets_in_serialized_summary(self):
        result = _build()
        text = json.dumps(result)
        for pattern in self._FORBIDDEN_PATTERNS:
            assert pattern not in text, (
                f"Forbidden pattern {pattern!r} found in summary JSON"
            )


# ── 18. Missing required fields raises RunSummaryError ───────────────────────

class TestMissingFieldsRaisesError:
    def test_missing_run_id_raises(self):
        gen = _gen_artifact()
        del gen["run_id"]
        with pytest.raises(RunSummaryError, match="run_id"):
            _build(gen_override=gen)

    def test_missing_benchmark_raises(self):
        gen = _gen_artifact()
        del gen["benchmark"]
        with pytest.raises(RunSummaryError, match="benchmark"):
            _build(gen_override=gen)

    def test_missing_task_id_raises(self):
        gen = _gen_artifact()
        del gen["task_id"]
        with pytest.raises(RunSummaryError, match="task_id"):
            _build(gen_override=gen)

    def test_missing_model_name_raises(self):
        gen = _gen_artifact()
        del gen["model_name"]
        with pytest.raises(RunSummaryError, match="model_name"):
            _build(gen_override=gen)

    def test_missing_extraction_status_raises(self):
        gen = _gen_artifact()
        del gen["extraction_status"]
        with pytest.raises(RunSummaryError, match="extraction_status"):
            _build(gen_override=gen)

    def test_missing_result_in_exec_raises(self):
        exec_ = _exec_artifact()
        del exec_["result"]
        with pytest.raises(RunSummaryError, match="result"):
            _build(exec_override=exec_)

    def test_missing_execution_performed_raises(self):
        exec_ = _exec_artifact()
        del exec_["result"]["execution_performed"]
        with pytest.raises(RunSummaryError, match="execution_performed"):
            _build(exec_override=exec_)

    def test_missing_tests_passed_raises(self):
        exec_ = _exec_artifact()
        del exec_["result"]["tests_passed"]
        with pytest.raises(RunSummaryError, match="tests_passed"):
            _build(exec_override=exec_)

    def test_missing_docker_used_raises(self):
        exec_ = _exec_artifact()
        del exec_["result"]["docker_used"]
        with pytest.raises(RunSummaryError, match="docker_used"):
            _build(exec_override=exec_)

    def test_missing_error_type_raises(self):
        exec_ = _exec_artifact()
        del exec_["result"]["error_type"]
        with pytest.raises(RunSummaryError, match="error_type"):
            _build(exec_override=exec_)

    def test_missing_timed_out_raises(self):
        exec_ = _exec_artifact()
        del exec_["result"]["timed_out"]
        with pytest.raises(RunSummaryError, match="timed_out"):
            _build(exec_override=exec_)

    def test_missing_execution_time_ms_raises(self):
        exec_ = _exec_artifact()
        del exec_["result"]["execution_time_ms"]
        with pytest.raises(RunSummaryError, match="execution_time_ms"):
            _build(exec_override=exec_)


# ── 19. Mismatched benchmark/task_id raises RunSummaryError ─────────────────

class TestIdentityMismatchRaisesError:
    def test_mismatched_benchmark_raises(self):
        gen = _gen_artifact(benchmark="tiny")
        exec_ = _exec_artifact(benchmark="mbpp")
        with pytest.raises(RunSummaryError, match="[Bb]enchmark mismatch"):
            build_run_summary(
                gen, exec_,
                generation_artifact_path="gen.json",
                execution_artifact_path="exec.json",
            )

    def test_mismatched_task_id_raises(self):
        gen = _gen_artifact(task_id="tiny_0")
        exec_ = _exec_artifact(task_id="tiny_1")
        with pytest.raises(RunSummaryError, match="task_id mismatch"):
            build_run_summary(
                gen, exec_,
                generation_artifact_path="gen.json",
                execution_artifact_path="exec.json",
            )

    def test_matching_benchmark_task_id_ok(self):
        gen = _gen_artifact(benchmark="tiny", task_id="tiny_0")
        exec_ = _exec_artifact(benchmark="tiny", task_id="tiny_0")
        result = build_run_summary(
            gen, exec_,
            generation_artifact_path="gen.json",
            execution_artifact_path="exec.json",
        )
        assert result["identity"]["benchmark"] == "tiny"
        assert result["identity"]["task_id"] == "tiny_0"


# ── 20. write_run_summary writes to tmp_path ─────────────────────────────────

class TestWriteRunSummary:
    def test_write_creates_file(self, tmp_path):
        summary = _build()
        path = write_run_summary(summary, output_dir=tmp_path)
        assert path.exists()

    def test_written_file_is_valid_json(self, tmp_path):
        summary = _build()
        path = write_run_summary(summary, output_dir=tmp_path)
        with open(path, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded["artifact_version"] == "4D.1"

    def test_written_file_roundtrip(self, tmp_path):
        summary = _build()
        path = write_run_summary(summary, output_dir=tmp_path)
        with open(path, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded["identity"] == summary["identity"]
        assert loaded["success"]["final_success"] == summary["success"]["final_success"]

    def test_write_returns_path_object(self, tmp_path):
        summary = _build()
        path = write_run_summary(summary, output_dir=tmp_path)
        assert isinstance(path, Path)

    def test_write_filename_contains_run_id_and_task_id(self, tmp_path):
        summary = _build()
        path = write_run_summary(summary, output_dir=tmp_path)
        assert "run_test_001" in path.name
        assert "tiny_0" in path.name
        assert "_summary.json" in path.name


# ── 21. Default output path uses ARTIFACTS_ROOT / run_summaries ───────────────

class TestDefaultOutputPath:
    def test_default_output_dir_is_under_artifacts_root(self, monkeypatch, tmp_path):
        import reliability_harness.artifacts.run_summary as rs_mod
        monkeypatch.setattr(rs_mod, "_RUN_SUMMARIES_ROOT", tmp_path / "run_summaries")
        summary = _build()
        path = write_run_summary(summary)
        assert (tmp_path / "run_summaries").is_dir()
        assert path.parent == (tmp_path / "run_summaries")


# ── 22. Sanitized filename handles task_id with slash ─────────────────────────

class TestSanitizedFilename:
    def test_slash_in_task_id_replaced_with_underscore(self, tmp_path):
        gen = _gen_artifact(task_id="HumanEval/0")
        exec_ = _exec_artifact(task_id="HumanEval/0")
        summary = build_run_summary(
            gen, exec_,
            generation_artifact_path="gen.json",
            execution_artifact_path="exec.json",
        )
        path = write_run_summary(summary, output_dir=tmp_path)
        assert "/" not in path.name
        assert "HumanEval_0" in path.name

    def test_slash_in_task_id_identity_preserved(self):
        gen = _gen_artifact(task_id="HumanEval/0")
        exec_ = _exec_artifact(task_id="HumanEval/0")
        summary = build_run_summary(
            gen, exec_,
            generation_artifact_path="gen.json",
            execution_artifact_path="exec.json",
        )
        # identity stores the original task_id, not the sanitized filename
        assert summary["identity"]["task_id"] == "HumanEval/0"

    def test_colon_in_task_id_sanitized(self, tmp_path):
        gen = _gen_artifact(task_id="task:001")
        exec_ = _exec_artifact(task_id="task:001")
        summary = build_run_summary(
            gen, exec_,
            generation_artifact_path="gen.json",
            execution_artifact_path="exec.json",
        )
        path = write_run_summary(summary, output_dir=tmp_path)
        assert ":" not in path.name


# ── load_json helper ──────────────────────────────────────────────────────────

class TestLoadJson:
    def test_load_valid_json(self, tmp_path):
        p = tmp_path / "artifact.json"
        p.write_text('{"key": "value"}', encoding="utf-8")
        data = load_json(p)
        assert data == {"key": "value"}

    def test_load_missing_file_raises(self, tmp_path):
        with pytest.raises(RunSummaryError, match="not found"):
            load_json(tmp_path / "nonexistent.json")

    def test_load_invalid_json_raises(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("not json {{{", encoding="utf-8")
        with pytest.raises(RunSummaryError, match="not valid JSON"):
            load_json(p)


# ── build_run_summary_from_paths convenience wrapper ─────────────────────────

class TestBuildFromPaths:
    def test_build_from_paths_returns_summary(self, tmp_path):
        gen_path = tmp_path / "gen.json"
        exec_path = tmp_path / "exec.json"
        gen_path.write_text(json.dumps(_gen_artifact()), encoding="utf-8")
        exec_path.write_text(json.dumps(_exec_artifact()), encoding="utf-8")
        result = build_run_summary_from_paths(gen_path, exec_path)
        assert result["artifact_version"] == "4D.1"
        assert result["identity"]["benchmark"] == "tiny"

    def test_build_from_paths_preserves_refs(self, tmp_path):
        gen_path = tmp_path / "gen.json"
        exec_path = tmp_path / "exec.json"
        gen_path.write_text(json.dumps(_gen_artifact()), encoding="utf-8")
        exec_path.write_text(json.dumps(_exec_artifact()), encoding="utf-8")
        result = build_run_summary_from_paths(gen_path, exec_path)
        assert str(gen_path) in result["artifact_refs"]["generation_artifact_path"]
        assert str(exec_path) in result["artifact_refs"]["execution_artifact_path"]

    def test_build_from_paths_missing_file_raises(self, tmp_path):
        with pytest.raises(RunSummaryError):
            build_run_summary_from_paths(
                tmp_path / "missing_gen.json",
                tmp_path / "missing_exec.json",
            )


# ── Benchmark-5A: metrics.process populated in run summary ───────────────────

class TestProcessMetricsInSummary:
    """Verify build_run_summary populates metrics.process (Benchmark-5A)."""

    def test_build_fills_metrics_process(self):
        result = _build()
        assert result["metrics"]["process"]
        assert isinstance(result["metrics"]["process"], dict)

    def test_observable_process_success_true_all_success(self):
        result = _build(
            _gen_artifact(extraction_status="success"),
            _exec_artifact(execution_performed=True, tests_passed=True),
        )
        assert result["metrics"]["process"]["observable_process_success"] is True

    def test_process_failure_stage_completed_all_success(self):
        result = _build(
            _gen_artifact(extraction_status="success"),
            _exec_artifact(execution_performed=True, tests_passed=True),
        )
        assert result["metrics"]["process"]["process_failure_stage"] == "completed"

    def test_process_failure_stage_extraction_on_extraction_failure(self):
        result = _build(
            _gen_artifact(extraction_status="failed", extracted_code=""),
            _exec_artifact(execution_performed=True, tests_passed=False),
        )
        assert result["metrics"]["process"]["process_failure_stage"] == "extraction"

    def test_process_failure_stage_execution_on_execution_failure(self):
        result = _build(
            _gen_artifact(extraction_status="success"),
            _exec_artifact(
                execution_performed=True,
                tests_passed=False,
                error_type="assertion_failure",
            ),
        )
        assert result["metrics"]["process"]["process_failure_stage"] == "execution"

    def test_metrics_recovery_remains_empty(self):
        result = _build()
        assert result["metrics"]["recovery"] == {}

    def test_metrics_memory_remains_empty(self):
        result = _build()
        assert result["metrics"]["memory"] == {}

    def test_diagnostics_failure_is_now_populated(self):
        result = _build()
        assert isinstance(result["diagnostics"]["failure"], dict)
        assert len(result["diagnostics"]["failure"]) > 0

    def test_success_is_process_reliability_metric_remains_false(self):
        result = _build()
        assert result["success"]["is_process_reliability_metric"] is False

    def test_summary_does_not_copy_raw_fields(self):
        forbidden = ("prompt", "raw_response", "extracted_code", "candidate_code",
                     "stdout", "stderr")
        result = _build()
        text = json.dumps(result)
        for key in forbidden:
            assert f'"{key}"' not in text, (
                f"Forbidden raw field {key!r} found in summary JSON"
            )


# ── Benchmark-5B: diagnostics.failure populated in run summary ────────────────

class TestFailureDiagnosticsInSummary:
    """Verify build_run_summary populates diagnostics.failure (Benchmark-5B)."""

    def test_build_fills_diagnostics_failure(self):
        result = _build()
        assert result["diagnostics"]["failure"]
        assert isinstance(result["diagnostics"]["failure"], dict)

    def test_success_failure_observed_false(self):
        result = _build(
            _gen_artifact(extraction_status="success"),
            _exec_artifact(execution_performed=True, tests_passed=True),
        )
        assert result["diagnostics"]["failure"]["failure_observed"] is False

    def test_success_failure_stage_none(self):
        result = _build(
            _gen_artifact(extraction_status="success"),
            _exec_artifact(execution_performed=True, tests_passed=True),
        )
        assert result["diagnostics"]["failure"]["failure_stage"] == "none"

    def test_extraction_failure_failure_stage_extraction(self):
        result = _build(
            _gen_artifact(extraction_status="failed", extracted_code=""),
            _exec_artifact(execution_performed=True, tests_passed=False),
        )
        assert result["diagnostics"]["failure"]["failure_stage"] == "extraction"

    def test_execution_failure_failure_stage_execution(self):
        result = _build(
            _gen_artifact(extraction_status="success"),
            _exec_artifact(
                execution_performed=True,
                tests_passed=False,
                error_type="assertion_failure",
            ),
        )
        assert result["diagnostics"]["failure"]["failure_stage"] == "execution"

    def test_timeout_failure_type_timeout(self):
        result = _build(
            _gen_artifact(extraction_status="success"),
            _exec_artifact(
                execution_performed=True,
                tests_passed=False,
                error_type="timeout",
                timed_out=True,
            ),
        )
        assert result["diagnostics"]["failure"]["failure_type"] == "timeout"

    def test_is_full_failure_taxonomy_false(self):
        result = _build()
        assert result["diagnostics"]["failure"]["is_full_failure_taxonomy"] is False

    def test_failure_diagnostics_does_not_overwrite_metrics_process(self):
        result = _build()
        assert "observable_process_success" in result["metrics"]["process"]

    def test_metrics_recovery_remains_empty(self):
        result = _build()
        assert result["metrics"]["recovery"] == {}

    def test_metrics_memory_remains_empty(self):
        result = _build()
        assert result["metrics"]["memory"] == {}

    def test_summary_does_not_copy_raw_fields(self):
        forbidden = ("prompt", "raw_response", "extracted_code", "candidate_code",
                     "stdout", "stderr")
        result = _build()
        text = json.dumps(result)
        for key in forbidden:
            assert f'"{key}"' not in text, (
                f"Forbidden raw field {key!r} found in summary JSON"
            )

    def test_success_is_process_reliability_metric_remains_false(self):
        result = _build()
        assert result["success"]["is_process_reliability_metric"] is False

    def test_metrics_process_is_full_process_reliability_metric_false(self):
        result = _build()
        assert result["metrics"]["process"]["is_full_process_reliability_metric"] is False
