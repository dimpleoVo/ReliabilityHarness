"""
Tests for reliability_harness.artifacts.generation_artifact.

No LLM calls. No Docker. No .env reading.
"""
import json
import pytest
from pathlib import Path

from reliability_harness.benchmarks.task_schema import BenchmarkTask
from reliability_harness.runtime.generation.code_extractor import CodeExtractionResult
from reliability_harness.artifacts.generation_artifact import (
    build_task_artifact,
    write_task_artifact,
    write_manifest,
)


def _make_task(task_id="tiny_0", benchmark="tiny"):
    return BenchmarkTask(
        task_id=task_id,
        benchmark=benchmark,
        prompt="Write a function that returns 42.",
        entry_point="solve",
    )


def _make_extraction(code="def solve(): return 42", status="success"):
    return CodeExtractionResult(extracted_code=code, extraction_status=status)


class TestBuildTaskArtifact:
    def test_has_all_required_fields(self):
        artifact = build_task_artifact(
            run_id="run_001",
            benchmark="tiny",
            task=_make_task(),
            model_name="deepseek-chat",
            prompt="test prompt",
            raw_response="```python\ndef solve(): return 42\n```",
            extraction=_make_extraction(),
        )
        required = [
            "run_id", "benchmark", "task_id", "model_name",
            "prompt", "raw_response", "extracted_code", "extraction_status",
            "error", "timestamp", "llm_used", "docker_used", "execution_performed",
        ]
        for field in required:
            assert field in artifact, f"Missing field: {field}"

    def test_docker_used_is_false(self):
        artifact = build_task_artifact(
            run_id="r1", benchmark="tiny", task=_make_task(), model_name="m",
            prompt="p", raw_response="r", extraction=_make_extraction(),
        )
        assert artifact["docker_used"] is False

    def test_execution_performed_is_false(self):
        artifact = build_task_artifact(
            run_id="r1", benchmark="tiny", task=_make_task(), model_name="m",
            prompt="p", raw_response="r", extraction=_make_extraction(),
        )
        assert artifact["execution_performed"] is False

    def test_llm_used_is_true(self):
        artifact = build_task_artifact(
            run_id="r1", benchmark="tiny", task=_make_task(), model_name="m",
            prompt="p", raw_response="r", extraction=_make_extraction(),
        )
        assert artifact["llm_used"] is True

    def test_no_api_key_in_artifact(self):
        artifact = build_task_artifact(
            run_id="r1", benchmark="tiny", task=_make_task(), model_name="deepseek-chat",
            prompt="p", raw_response="r", extraction=_make_extraction(),
        )
        serialized = json.dumps(artifact).lower()
        assert "api_key" not in serialized

    def test_task_id_matches(self):
        artifact = build_task_artifact(
            run_id="r1", benchmark="tiny", task=_make_task(task_id="tiny_42"), model_name="m",
            prompt="p", raw_response="r", extraction=_make_extraction(),
        )
        assert artifact["task_id"] == "tiny_42"

    def test_model_name_matches(self):
        artifact = build_task_artifact(
            run_id="r1", benchmark="tiny", task=_make_task(), model_name="deepseek-chat",
            prompt="p", raw_response="r", extraction=_make_extraction(),
        )
        assert artifact["model_name"] == "deepseek-chat"

    def test_extraction_status_propagated(self):
        extraction = CodeExtractionResult(extracted_code=None, extraction_status="no_code_block")
        artifact = build_task_artifact(
            run_id="r1", benchmark="tiny", task=_make_task(), model_name="m",
            prompt="p", raw_response="no fence", extraction=extraction,
        )
        assert artifact["extraction_status"] == "no_code_block"
        assert artifact["extracted_code"] is None


class TestWriteTaskArtifact:
    def test_writes_json_file(self, tmp_path):
        artifact = build_task_artifact(
            run_id="r1", benchmark="tiny", task=_make_task(), model_name="m",
            prompt="p", raw_response="r", extraction=_make_extraction(),
        )
        path = write_task_artifact(artifact, tmp_path)
        assert Path(path).exists()

    def test_written_file_is_valid_json(self, tmp_path):
        artifact = build_task_artifact(
            run_id="r1", benchmark="tiny", task=_make_task(), model_name="m",
            prompt="p", raw_response="r", extraction=_make_extraction(),
        )
        path = write_task_artifact(artifact, tmp_path)
        with open(path, encoding="utf-8") as f:
            content = json.load(f)
        assert content["task_id"] == "tiny_0"

    def test_file_named_after_task_id(self, tmp_path):
        artifact = build_task_artifact(
            run_id="r1", benchmark="tiny", task=_make_task(task_id="my_task"), model_name="m",
            prompt="p", raw_response="r", extraction=_make_extraction(),
        )
        path = write_task_artifact(artifact, tmp_path)
        assert "my_task" in Path(path).name

    def test_task_id_slash_sanitized(self, tmp_path):
        artifact = build_task_artifact(
            run_id="r1", benchmark="humaneval", task=_make_task(task_id="HumanEval/0"), model_name="m",
            prompt="p", raw_response="r", extraction=_make_extraction(),
        )
        path = write_task_artifact(artifact, tmp_path)
        assert "/" not in Path(path).name


class TestWriteManifest:
    def test_manifest_written_to_disk(self, tmp_path):
        write_manifest(
            run_id="r1", benchmark="tiny", model_name="m",
            num_tasks=2, artifact_paths=["a.json", "b.json"], run_dir=tmp_path,
        )
        assert (tmp_path / "manifest.json").exists()

    def test_manifest_has_required_fields(self, tmp_path):
        manifest = write_manifest(
            run_id="r1", benchmark="tiny", model_name="m",
            num_tasks=2, artifact_paths=["a.json", "b.json"], run_dir=tmp_path,
        )
        for field in [
            "run_id", "benchmark", "model_name", "num_tasks",
            "artifacts", "llm_used", "docker_used", "execution_performed",
        ]:
            assert field in manifest, f"Missing field: {field}"

    def test_manifest_docker_used_false(self, tmp_path):
        manifest = write_manifest(
            run_id="r1", benchmark="tiny", model_name="m",
            num_tasks=0, artifact_paths=[], run_dir=tmp_path,
        )
        assert manifest["docker_used"] is False

    def test_manifest_execution_performed_false(self, tmp_path):
        manifest = write_manifest(
            run_id="r1", benchmark="tiny", model_name="m",
            num_tasks=0, artifact_paths=[], run_dir=tmp_path,
        )
        assert manifest["execution_performed"] is False

    def test_manifest_llm_used_true(self, tmp_path):
        manifest = write_manifest(
            run_id="r1", benchmark="tiny", model_name="m",
            num_tasks=0, artifact_paths=[], run_dir=tmp_path,
        )
        assert manifest["llm_used"] is True

    def test_manifest_path_returned(self, tmp_path):
        manifest = write_manifest(
            run_id="r1", benchmark="tiny", model_name="m",
            num_tasks=0, artifact_paths=[], run_dir=tmp_path,
        )
        assert "manifest_path" in manifest
        assert Path(manifest["manifest_path"]).exists()

    def test_manifest_json_on_disk_valid(self, tmp_path):
        write_manifest(
            run_id="r1", benchmark="tiny", model_name="m",
            num_tasks=3, artifact_paths=["x.json"], run_dir=tmp_path,
        )
        with open(tmp_path / "manifest.json", encoding="utf-8") as f:
            content = json.load(f)
        assert content["num_tasks"] == 3
        assert content["run_id"] == "r1"
