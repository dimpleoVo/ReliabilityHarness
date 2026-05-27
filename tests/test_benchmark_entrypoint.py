"""
Root-level tests for reliability_harness.experiments.run_benchmark.

Migration-4A/B: These tests replace ReActX/test_*.py as the authoritative
constraint on the Benchmark-0 pipeline skeleton.

No LLM calls. No Docker. No data loading. No ReActX/app/evalforge imports.
"""
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
