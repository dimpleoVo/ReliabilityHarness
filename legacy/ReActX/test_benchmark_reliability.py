import json
import tempfile
from pathlib import Path

import benchmark_reliability as bench


def assert_task_result_schema(result):
    for field in bench.REQUIRED_RESULT_FIELDS:
        assert field in result, f"missing result field: {field}"


def main():
    tasks = bench.load_tasks()
    assert tasks, "reliability_tasks.json should load at least one task"

    limited = bench.load_tasks(limit=5)
    assert len(limited) == 5, f"BENCHMARK_LIMIT behavior failed: {len(limited)}"

    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "benchmark_results"

        single = bench.run_task_mock(tasks[0], output_dir=output_dir)
        assert_task_result_schema(single)
        assert isinstance(single["recovered"], bool), "recovered field must be bool"
        assert isinstance(single["trajectory_analysis"], dict), "trajectory_analysis must be present"
        assert "recovery_type" in single["trajectory_analysis"], "recovery_type missing"
        assert "trajectory_quality" in single["trajectory_analysis"], "trajectory_quality missing"

        rr_task = {
            "id": "rr_test",
            "category": "recoverable_retry",
            "task": "print 42",
            "expected_output": "42",
            "failure_mode": "semantic_error",
            "difficulty": "easy",
            "why_relevant": "test",
            "evaluation": {"metric": "exact_match", "direction": "higher_is_better"},
        }
        rr_result = bench.run_task_mock(rr_task, output_dir=output_dir)
        assert isinstance(rr_result["recovered"], bool), "recovered must be bool for recoverable_retry"
        assert rr_result["recovered"] is True, "recoverable_retry task must produce recovered=True"
        assert rr_result["trajectory_analysis"]["recovery_type"] == "semantic_fix", rr_result
        assert rr_result["trajectory_analysis"]["trajectory_quality"] == "good", rr_result
        rr_summary = bench.aggregate_results([rr_result])
        assert rr_summary["recovery_rate"] > 0, (
            f"recovery_rate should be > 0 when recoverable_retry tasks are included, got {rr_summary['recovery_rate']}"
        )

        sample_results = [
            {
                "id": "a",
                "category": "runtime_error",
                "task": "task a",
                "expected_output": "1",
                "success": True,
                "num_attempts": 1,
                "final_output": "1",
                "final_score": 1.0,
                "failure_mode": "runtime_error",
                "runtime_error": False,
                "timeout": False,
                "recovered": False,
                "artifact_path": "",
                "error_summary": "",
                "trajectory_analysis": {
                    "recovery_type": "unknown",
                    "trajectory_quality": "partial",
                    "repeated_same_failure": False,
                },
            },
            {
                "id": "b",
                "category": "semantic_error",
                "task": "task b",
                "expected_output": "2",
                "success": False,
                "num_attempts": 3,
                "final_output": "",
                "final_score": 0.0,
                "failure_mode": "semantic_error",
                "runtime_error": False,
                "timeout": False,
                "recovered": False,
                "artifact_path": "",
                "error_summary": "wrong output",
                "trajectory_analysis": {
                    "recovery_type": "unrecovered",
                    "trajectory_quality": "poor",
                    "repeated_same_failure": True,
                },
            },
        ]
        summary = bench.aggregate_results(sample_results)
        assert summary["total_tasks"] == 2, summary
        assert summary["success_rate"] == 0.5, summary
        assert "runtime_error" in summary["category_metrics"], summary
        assert summary["category_metrics"]["runtime_error"]["total_tasks"] == 1, summary
        assert summary["category_metrics"]["semantic_error"]["success_rate"] == 0.0, summary

        paths = bench.write_benchmark_outputs(sample_results, summary, output_dir=output_dir)
        json_path = Path(paths["json"])
        md_path = Path(paths["markdown"])
        assert json_path.exists(), f"missing JSON output: {json_path}"
        assert md_path.exists(), f"missing Markdown output: {md_path}"

        with open(json_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        assert payload["summary"]["total_tasks"] == 2, payload

        md = md_path.read_text(encoding="utf-8")
        assert "## Trajectory Reasoning" in md, md
        assert "recovery_type" in md, md
        assert "trajectory_quality" in md, md
        assert "repeated_same_failure" in md, md
        assert "## Failed Tasks" in md, md
        assert "b [semantic_error]" in md, md

        empty_summary = bench.aggregate_results([])
        assert empty_summary["total_tasks"] == 0, empty_summary
        assert empty_summary["success_rate"] == 0.0, empty_summary

        run = bench.run_benchmark(limit=3, mock=True, output_dir=output_dir)
        assert run["summary"]["total_tasks"] == 3, run["summary"]
        for result in run["results"]:
            assert "trajectory_analysis" in result, result
            assert "recovery_type" in result["trajectory_analysis"], result
            assert "trajectory_quality" in result["trajectory_analysis"], result
        assert Path(run["paths"]["json"]).exists(), run["paths"]
        assert Path(run["paths"]["markdown"]).exists(), run["paths"]

    print("[TEST PASS] benchmark_reliability mock runner passed")


if __name__ == "__main__":
    main()
