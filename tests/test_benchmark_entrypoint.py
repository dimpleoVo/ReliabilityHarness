"""
Root-level tests for reliability_harness.experiments.run_benchmark.

Migration-4A/B: These tests replace ReActX/test_*.py as the authoritative
constraint on the Benchmark-0 pipeline skeleton.

No LLM calls. No Docker. No data loading. No ReActX/app/evalforge imports.
"""
import json
import os

import pytest

from reliability_harness.experiments.run_benchmark import dry_run, run


class TestDryRun:
    def test_mbpp_dry_run_returns_summary(self):
        result = dry_run("mbpp")
        assert isinstance(result, dict)
        assert result["benchmark"] == "mbpp"
        assert result["status"] == "dry-run skeleton"
        assert result["project"] == "ReliabilityHarness"

    def test_mbpp_dry_run_adapter_name(self):
        result = dry_run("mbpp")
        assert result["adapter"] == "MBPPAdapter"

    def test_humaneval_dry_run_returns_summary(self):
        result = dry_run("humaneval")
        assert isinstance(result, dict)
        assert result["benchmark"] == "humaneval"
        assert result["status"] == "dry-run skeleton"
        assert result["project"] == "ReliabilityHarness"

    def test_humaneval_dry_run_adapter_name(self):
        result = dry_run("humaneval")
        assert result["adapter"] == "HumanEvalAdapter"

    def test_dry_run_contains_pipeline(self):
        result = dry_run("mbpp")
        assert "pipeline" in result
        assert isinstance(result["pipeline"], list)
        assert len(result["pipeline"]) > 0

    def test_dry_run_contains_path_fields(self):
        result = dry_run("mbpp")
        assert "data_root" in result
        assert "output_root" in result
        assert "runs_output" in result
        assert "reports_output" in result


class TestRunDispatch:
    def test_run_with_dry_run_mode_mbpp(self):
        result = run("mbpp", dry_run_mode=True)
        assert result["benchmark"] == "mbpp"
        assert result["status"] == "dry-run skeleton"

    def test_run_with_dry_run_mode_humaneval(self):
        result = run("humaneval", dry_run_mode=True)
        assert result["benchmark"] == "humaneval"
        assert result["status"] == "dry-run skeleton"

    def test_run_full_mbpp_raises_not_implemented(self):
        with pytest.raises(NotImplementedError):
            run("mbpp", dry_run_mode=False)

    def test_run_full_humaneval_raises_not_implemented(self):
        with pytest.raises(NotImplementedError):
            run("humaneval", dry_run_mode=False)


class TestTinyDryRun:
    def test_tiny_dry_run_returns_benchmark_name(self):
        result = dry_run("tiny")
        assert result["benchmark"] == "tiny"

    def test_tiny_dry_run_returns_adapter_name(self):
        result = dry_run("tiny")
        assert result["adapter"] == "TinyFixtureAdapter"

    def test_tiny_dry_run_status(self):
        result = dry_run("tiny")
        assert result["status"] == "dry-run skeleton"

    def test_tiny_dry_run_contains_benchmark_results_output(self):
        result = dry_run("tiny")
        assert "benchmark_results_output" in result

    def test_tiny_dry_run_contains_dry_run_artifact(self):
        result = dry_run("tiny")
        assert "dry_run_artifact" in result

    def test_tiny_dry_run_artifact_path_ends_correctly(self):
        result = dry_run("tiny")
        artifact = result["dry_run_artifact"]
        assert artifact.endswith(
            os.path.join("benchmark_results", "tiny_dry_run.json")
        )

    def test_tiny_dry_run_artifact_file_exists(self):
        result = dry_run("tiny")
        assert os.path.isfile(result["dry_run_artifact"])

    def test_tiny_dry_run_artifact_json_contains_benchmark(self):
        result = dry_run("tiny")
        with open(result["dry_run_artifact"], encoding="utf-8") as f:
            content = json.load(f)
        assert content["benchmark"] == "tiny"

    def test_tiny_dry_run_artifact_json_contains_adapter(self):
        result = dry_run("tiny")
        with open(result["dry_run_artifact"], encoding="utf-8") as f:
            content = json.load(f)
        assert content["adapter"] == "TinyFixtureAdapter"

    def test_tiny_dry_run_num_tasks(self):
        result = dry_run("tiny")
        assert result["num_tasks"] == 2

    def test_run_tiny_dry_run_mode_matches(self):
        result = run("tiny", dry_run_mode=True)
        assert result["benchmark"] == "tiny"
        assert result["status"] == "dry-run skeleton"
        assert "dry_run_artifact" in result
