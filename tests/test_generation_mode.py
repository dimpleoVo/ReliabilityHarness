"""
Integration tests for Benchmark-3 generation mode (generate_for_tasks).

Uses mock LLM — no real API calls, no .env reading, no Docker, no sandbox.
Tests dry-run isolation, artifact writing, manifest structure, mock LLM path.
"""
import importlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from reliability_harness.benchmarks.task_schema import BenchmarkTask
from reliability_harness.runtime.generation.generator import generate_for_tasks
from reliability_harness.runtime.generation.code_extractor import CodeExtractionResult


class _MockLLMClient:
    """Test double for LLMClient — never calls a real API."""

    def __init__(self, response: str = "```python\ndef solve(): return 42\n```"):
        self.model_name = "mock-model"
        self._response = response
        self.call_count = 0

    def generate(self, prompt: str) -> str:
        self.call_count += 1
        return self._response


def _make_task(task_id: str = "tiny_0", benchmark: str = "tiny") -> BenchmarkTask:
    return BenchmarkTask(
        task_id=task_id,
        benchmark=benchmark,
        prompt="Write a function that returns 42.",
        entry_point="solve",
        tests=["assert solve() == 42"],
    )


class TestGenerateForTasksWithMock:
    def test_writes_manifest_json(self, tmp_path):
        tasks = [_make_task()]
        client = _MockLLMClient()
        manifest = generate_for_tasks(tasks, client, "mock-model", output_root=tmp_path)
        assert Path(manifest["manifest_path"]).exists()

    def test_writes_task_artifact_per_task(self, tmp_path):
        tasks = [_make_task()]
        client = _MockLLMClient()
        manifest = generate_for_tasks(tasks, client, "mock-model", output_root=tmp_path)
        assert len(manifest["artifacts"]) == 1
        assert Path(manifest["artifacts"][0]).exists()

    def test_calls_llm_once_per_task(self, tmp_path):
        tasks = [_make_task("t0"), _make_task("t1")]
        client = _MockLLMClient()
        generate_for_tasks(tasks, client, "mock-model", output_root=tmp_path)
        assert client.call_count == 2

    def test_respects_limit(self, tmp_path):
        tasks = [_make_task("t0"), _make_task("t1"), _make_task("t2")]
        client = _MockLLMClient()
        manifest = generate_for_tasks(tasks, client, "mock-model", output_root=tmp_path, limit=1)
        assert manifest["num_tasks"] == 1
        assert client.call_count == 1

    def test_manifest_llm_used_true(self, tmp_path):
        tasks = [_make_task()]
        manifest = generate_for_tasks(tasks, _MockLLMClient(), "mock-model", output_root=tmp_path)
        assert manifest["llm_used"] is True

    def test_manifest_docker_used_false(self, tmp_path):
        tasks = [_make_task()]
        manifest = generate_for_tasks(tasks, _MockLLMClient(), "mock-model", output_root=tmp_path)
        assert manifest["docker_used"] is False

    def test_manifest_execution_performed_false(self, tmp_path):
        tasks = [_make_task()]
        manifest = generate_for_tasks(tasks, _MockLLMClient(), "mock-model", output_root=tmp_path)
        assert manifest["execution_performed"] is False

    def test_artifact_has_no_api_key(self, tmp_path):
        tasks = [_make_task()]
        manifest = generate_for_tasks(tasks, _MockLLMClient(), "mock-model", output_root=tmp_path)
        with open(manifest["artifacts"][0], encoding="utf-8") as f:
            artifact = json.load(f)
        assert "api_key" not in json.dumps(artifact).lower()

    def test_artifact_docker_used_false(self, tmp_path):
        tasks = [_make_task()]
        manifest = generate_for_tasks(tasks, _MockLLMClient(), "mock-model", output_root=tmp_path)
        with open(manifest["artifacts"][0], encoding="utf-8") as f:
            artifact = json.load(f)
        assert artifact["docker_used"] is False

    def test_artifact_execution_performed_false(self, tmp_path):
        tasks = [_make_task()]
        manifest = generate_for_tasks(tasks, _MockLLMClient(), "mock-model", output_root=tmp_path)
        with open(manifest["artifacts"][0], encoding="utf-8") as f:
            artifact = json.load(f)
        assert artifact["execution_performed"] is False

    def test_run_id_directory_created(self, tmp_path):
        tasks = [_make_task()]
        manifest = generate_for_tasks(tasks, _MockLLMClient(), "mock-model", output_root=tmp_path)
        run_dir = Path(manifest["manifest_path"]).parent
        assert run_dir.is_dir()

    def test_extraction_status_in_artifact(self, tmp_path):
        tasks = [_make_task()]
        manifest = generate_for_tasks(tasks, _MockLLMClient(), "mock-model", output_root=tmp_path)
        with open(manifest["artifacts"][0], encoding="utf-8") as f:
            artifact = json.load(f)
        assert artifact["extraction_status"] == "success"
        assert artifact["extracted_code"] is not None


class TestDryRunDoesNotCallLLM:
    def test_dry_run_succeeds_without_api_key(self, monkeypatch):
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        from reliability_harness.experiments.run_benchmark import run
        result = run("tiny", dry_run_mode=True)
        assert result["benchmark"] == "tiny"
        assert result["status"] == "dry-run skeleton"

    def test_dry_run_result_has_no_llm_used_field(self):
        from reliability_harness.experiments.run_benchmark import run
        result = run("tiny", dry_run_mode=True)
        assert "llm_used" not in result

    def test_dry_run_does_not_import_generate_path(self, monkeypatch):
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        # Mock from_env so if it IS called, it would fail loudly
        with patch(
            "reliability_harness.runtime.generation.llm_client.LLMClient.from_env",
            side_effect=AssertionError("from_env must not be called in dry-run"),
        ):
            from reliability_harness.experiments.run_benchmark import run
            result = run("tiny", dry_run_mode=True)
        assert result["benchmark"] == "tiny"


class TestLLMClientImportSafety:
    def test_import_does_not_raise_without_api_key(self, monkeypatch):
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        # Reload to simulate cold import
        mod_name = "reliability_harness.runtime.generation.llm_client"
        sys.modules.pop(mod_name, None)
        mod = importlib.import_module(mod_name)
        assert hasattr(mod, "LLMClient")

    def test_from_env_raises_without_key(self, monkeypatch):
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        with patch("dotenv.load_dotenv"):
            from reliability_harness.runtime.generation.llm_client import LLMClient
            with pytest.raises(RuntimeError, match="DEEPSEEK_API_KEY"):
                LLMClient.from_env()
