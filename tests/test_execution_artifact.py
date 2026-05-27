"""Tests for reliability_harness.artifacts.execution_artifact.

No LLM calls. No Docker. No .env reading.
"""
import json
import pytest
from pathlib import Path

from reliability_harness.runtime.execution.contract import ExecutionInput, ExecutionResult
from reliability_harness.artifacts.execution_artifact import (
    build_execution_artifact,
    write_execution_artifact,
)


def _make_input(**kwargs) -> ExecutionInput:
    defaults = dict(
        run_id="run_4a_001",
        benchmark="mbpp",
        task_id="mbpp_1",
        candidate_code="def add(a, b): return a + b",
        tests=["assert add(1, 2) == 3"],
        source_generation_artifact=None,
    )
    defaults.update(kwargs)
    return ExecutionInput(**defaults)


def _make_result(**kwargs) -> ExecutionResult:
    defaults = dict(
        run_id="run_4a_001",
        benchmark="mbpp",
        task_id="mbpp_1",
        exit_code=0,
        stdout="",
        stderr="",
        timed_out=False,
        tests_passed=True,
        error_type=None,
        execution_time_ms=15,
        docker_used=False,
        execution_performed=True,
    )
    defaults.update(kwargs)
    return ExecutionResult(**defaults)


class TestBuildExecutionArtifact:
    def test_has_required_top_level_fields(self):
        artifact = build_execution_artifact(_make_input(), _make_result())
        required = [
            "run_id", "benchmark", "task_id",
            "candidate_code", "tests",
            "result", "artifact_version", "created_at",
            "source_generation_artifact",
        ]
        for field in required:
            assert field in artifact, f"Missing field: {field}"

    def test_result_has_required_fields(self):
        artifact = build_execution_artifact(_make_input(), _make_result())
        result = artifact["result"]
        for field in [
            "exit_code", "stdout", "stderr",
            "timed_out", "tests_passed", "error_type",
            "execution_time_ms", "docker_used", "execution_performed",
        ]:
            assert field in result, f"Missing result field: {field}"

    def test_run_id_matches(self):
        artifact = build_execution_artifact(
            _make_input(run_id="my_run"),
            _make_result(run_id="my_run"),
        )
        assert artifact["run_id"] == "my_run"

    def test_benchmark_matches(self):
        artifact = build_execution_artifact(
            _make_input(benchmark="humaneval"),
            _make_result(benchmark="humaneval"),
        )
        assert artifact["benchmark"] == "humaneval"

    def test_task_id_matches(self):
        artifact = build_execution_artifact(
            _make_input(task_id="mbpp_99"),
            _make_result(task_id="mbpp_99"),
        )
        assert artifact["task_id"] == "mbpp_99"

    def test_tests_passed_in_result(self):
        artifact = build_execution_artifact(_make_input(), _make_result(tests_passed=True))
        assert artifact["result"]["tests_passed"] is True

    def test_docker_used_false_in_result(self):
        artifact = build_execution_artifact(_make_input(), _make_result(docker_used=False))
        assert artifact["result"]["docker_used"] is False

    def test_execution_performed_true_in_result(self):
        artifact = build_execution_artifact(_make_input(), _make_result(execution_performed=True))
        assert artifact["result"]["execution_performed"] is True

    def test_artifact_version_present(self):
        artifact = build_execution_artifact(_make_input(), _make_result())
        assert artifact["artifact_version"] == "4A.1"

    def test_source_generation_artifact_none(self):
        artifact = build_execution_artifact(_make_input(source_generation_artifact=None), _make_result())
        assert artifact["source_generation_artifact"] is None

    def test_source_generation_artifact_propagated(self):
        path = "outputs/predictions/run_x/mbpp_1.json"
        artifact = build_execution_artifact(
            _make_input(source_generation_artifact=path), _make_result()
        )
        assert artifact["source_generation_artifact"] == path

    def test_no_api_key_in_artifact(self):
        artifact = build_execution_artifact(_make_input(), _make_result())
        serialized = json.dumps(artifact).lower()
        assert "deepseek_api_key" not in serialized
        assert "api_key" not in serialized

    def test_no_sk_prefix_token(self):
        artifact = build_execution_artifact(_make_input(), _make_result())
        serialized = json.dumps(artifact)
        assert "sk-" not in serialized

    def test_no_env_reference(self):
        artifact = build_execution_artifact(_make_input(), _make_result())
        serialized = json.dumps(artifact).lower()
        assert ".env" not in serialized

    def test_candidate_code_in_artifact(self):
        artifact = build_execution_artifact(
            _make_input(candidate_code="def f(): return 7"), _make_result()
        )
        assert "def f(): return 7" in artifact["candidate_code"]

    def test_tests_list_in_artifact(self):
        artifact = build_execution_artifact(
            _make_input(tests=["assert True"]), _make_result()
        )
        assert artifact["tests"] == ["assert True"]


class TestWriteExecutionArtifact:
    def test_writes_json_file(self, tmp_path):
        artifact = build_execution_artifact(_make_input(), _make_result())
        path = write_execution_artifact(artifact, tmp_path)
        assert path.exists()

    def test_written_file_is_valid_json(self, tmp_path):
        artifact = build_execution_artifact(_make_input(), _make_result())
        path = write_execution_artifact(artifact, tmp_path)
        with open(path, encoding="utf-8") as f:
            content = json.load(f)
        assert content["run_id"] == "run_4a_001"

    def test_creates_output_dir(self, tmp_path):
        subdir = tmp_path / "executions" / "run_001"
        artifact = build_execution_artifact(_make_input(), _make_result())
        path = write_execution_artifact(artifact, subdir)
        assert path.parent == subdir
        assert subdir.exists()

    def test_file_named_with_run_id_and_task_id(self, tmp_path):
        artifact = build_execution_artifact(
            _make_input(run_id="run_x", task_id="mbpp_7"),
            _make_result(run_id="run_x", task_id="mbpp_7"),
        )
        path = write_execution_artifact(artifact, tmp_path)
        assert "run_x" in path.name
        assert "mbpp_7" in path.name

    def test_slash_in_task_id_sanitized(self, tmp_path):
        artifact = build_execution_artifact(
            _make_input(task_id="HumanEval/42"),
            _make_result(task_id="HumanEval/42"),
        )
        path = write_execution_artifact(artifact, tmp_path)
        assert "/" not in path.name

    def test_returns_path_object(self, tmp_path):
        artifact = build_execution_artifact(_make_input(), _make_result())
        path = write_execution_artifact(artifact, tmp_path)
        assert isinstance(path, Path)

    def test_outputs_executions_style_path(self, tmp_path):
        executions_dir = tmp_path / "outputs" / "executions" / "run_4a_001"
        artifact = build_execution_artifact(_make_input(), _make_result())
        path = write_execution_artifact(artifact, executions_dir)
        assert path.exists()
        assert "executions" in str(path)
