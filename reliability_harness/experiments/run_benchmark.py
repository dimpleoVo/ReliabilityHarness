"""
ReliabilityHarness — formal paper benchmark entrypoint.

THIS IS THE SOLE ENTRYPOINT for ReliabilityHarness paper experiments.
Do NOT use ReActX/benchmark_reliability.py or run_eval.py for paper results.
Those files are legacy / EvalForge-era scripts that are not connected to the
ReliabilityHarness process-aware evaluation pipeline.

Usage
-----
Dry-run (validate pipeline skeleton, no data loading, no LLM calls):
    python -m reliability_harness.experiments.run_benchmark --benchmark mbpp --dry-run
    python -m reliability_harness.experiments.run_benchmark --benchmark humaneval --dry-run

Full run (not yet implemented — MBPP/HumanEval loading coming next phase):
    python -m reliability_harness.experiments.run_benchmark --benchmark mbpp

Pipeline (once fully implemented)
----------------------------------
Step 1  adapter            load + normalise tasks via BenchmarkAdapter
Step 2  task normalisation map to BenchmarkTask schema
Step 3  runtime execution  closed-loop agent (reliability_harness.runtime)
Step 4  sandbox execution  Docker-isolated test execution (reliability_harness.sandbox)
Step 5  trajectory capture reliability_harness.runtime.agent.trajectory
Step 6  process evaluation reliability_harness.evaluation.runtime_eval
Step 7  artifact writing   reliability_harness.artifacts.run_artifact → outputs/runs/
Step 8  report generation  reliability_harness.reporting.reliability_report → outputs/reports/

Path policy
-----------
- Task fixtures:        data/tasks/
- Experiment fixtures:  data/fixtures/
- Run artifacts:        outputs/runs/
- Reliability reports:  outputs/reports/
- Benchmark summaries:  outputs/benchmark_results/
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from reliability_harness.benchmarks.registry import get_adapter, list_benchmarks
from reliability_harness.utils.paths import (
    BENCHMARK_RESULTS_ROOT,
    DATA_ROOT,
    OUTPUTS_ROOT,
    REPORTS_ROOT,
    RUNS_ROOT,
    TASKS_ROOT,
)


def dry_run(benchmark: str) -> dict[str, Any]:
    """Return the pipeline manifest without loading any data or running experiments.

    For benchmarks with a loadable fixture (e.g. tiny), also writes the manifest
    to outputs/benchmark_results/<benchmark>_dry_run.json and adds a
    dry_run_artifact field to the returned dict.

    For skeleton adapters (mbpp, humaneval) that raise NotImplementedError on
    load_tasks(), no file is written.
    """
    adapter = get_adapter(benchmark)

    # Try to load tasks — succeeds for fixture-backed adapters (tiny),
    # raises NotImplementedError for skeleton adapters (mbpp, humaneval).
    try:
        tasks = adapter.load_tasks()
        num_tasks = len(tasks)
    except NotImplementedError:
        num_tasks = None

    manifest: dict[str, Any] = {
        "project": "ReliabilityHarness",
        "benchmark": benchmark,
        "adapter": type(adapter).__name__,
        "status": "dry-run skeleton",
        "data_root": str(DATA_ROOT),
        "tasks_root": str(TASKS_ROOT),
        "fixture_root": str(DATA_ROOT / "fixtures"),
        "output_root": str(OUTPUTS_ROOT),
        "runs_output": str(RUNS_ROOT),
        "reports_output": str(REPORTS_ROOT),
        "benchmark_results_output": str(BENCHMARK_RESULTS_ROOT),
        "num_tasks": num_tasks,
        "pipeline": [
            "1. adapter            — load + normalise tasks via BenchmarkAdapter",
            "2. task normalisation — map to BenchmarkTask schema",
            "3. runtime execution  — closed-loop agent",
            "4. sandbox execution  — Docker-isolated test execution",
            "5. trajectory capture",
            "6. process-aware evaluation",
            "7. artifact writing   → outputs/runs/",
            "8. report generation  → outputs/reports/",
        ],
    }

    # Write artifact for fixture-backed benchmarks
    if num_tasks is not None:
        artifact_path = BENCHMARK_RESULTS_ROOT / f"{benchmark}_dry_run.json"
        BENCHMARK_RESULTS_ROOT.mkdir(parents=True, exist_ok=True)
        with open(artifact_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        manifest["dry_run_artifact"] = str(artifact_path)

    return manifest


def run(
    benchmark: str,
    dry_run_mode: bool = False,
    **kwargs: Any,
) -> dict[str, Any]:
    """Main benchmark run entry point.

    Parameters
    ----------
    benchmark:
        Benchmark name, e.g. "mbpp" or "humaneval".
    dry_run_mode:
        If True, return the pipeline manifest without loading data.
    **kwargs:
        Reserved for future options (split, limit, output_dir, etc.).

    Returns
    -------
    dict
        Dry-run manifest or future run summary.

    Raises
    ------
    NotImplementedError
        When dry_run_mode is False (full execution not yet implemented).
    """
    if dry_run_mode:
        return dry_run(benchmark)

    raise NotImplementedError(
        f"Full execution for benchmark={benchmark!r} is not yet implemented. "
        "Complete MBPP/HumanEval execution will be added in the next benchmark phase. "
        "Use --dry-run to validate the pipeline skeleton without loading data."
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m reliability_harness.experiments.run_benchmark",
        description=(
            "ReliabilityHarness paper benchmark runner. "
            "Use --dry-run to validate the pipeline skeleton."
        ),
    )
    parser.add_argument(
        "--benchmark",
        required=True,
        choices=list_benchmarks(),
        metavar="BENCHMARK",
        help=f"Benchmark to run. Supported: {', '.join(list_benchmarks())}",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help=(
            "Print the pipeline skeleton manifest without loading data, "
            "calling LLMs, or writing outputs."
        ),
    )
    args = parser.parse_args(argv)
    result = run(benchmark=args.benchmark, dry_run_mode=args.dry_run)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
