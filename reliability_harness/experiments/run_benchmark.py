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

Generation mode (Benchmark-3 — LLM candidate generation, no execution):
    python -m reliability_harness.experiments.run_benchmark --benchmark tiny --generate
    python -m reliability_harness.experiments.run_benchmark --benchmark tiny --generate --limit 1 --model-name deepseek-chat

Aggregate run summaries (Benchmark-6B.1 — aggregate multiple run summary artifacts):
    python -m reliability_harness.experiments.run_benchmark --aggregate-run-summaries outputs/artifacts/run_summaries/*.json

Full run (not yet implemented — process evaluation coming next phase):
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
- Generation outputs:   outputs/predictions/{run_id}/
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
    """Return the pipeline manifest without calling LLMs, Docker, memory, or executing code.

    All registered benchmarks (tiny, mbpp, humaneval) are fixture-backed and load
    tasks from local JSON files under data/fixtures/. dry_run() loads tasks only to
    report num_tasks; it does not run agents, sandboxes, or any external services.

    For fixture-backed benchmarks, also writes the manifest to
    outputs/benchmark_results/<benchmark>_dry_run.json and adds a
    dry_run_artifact field to the returned dict.

    If a future adapter raises NotImplementedError on load_tasks(), num_tasks is
    reported as None and no artifact file is written.
    """
    adapter = get_adapter(benchmark)

    # Load tasks from local fixture to report num_tasks.
    # Fixture-backed adapters (tiny, mbpp, humaneval) always succeed here.
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


def _execute_generate(
    benchmark: str,
    limit: int | None,
    model_name: str,
    temperature: float,
    max_tokens: int,
) -> dict[str, Any]:
    """Run generation-only LLM candidate generation (Benchmark-3).

    Deferred imports ensure the dry-run path never imports LLMClient or
    triggers load_dotenv(). Requires DEEPSEEK_API_KEY in environment or .env.
    """
    # Deferred: dry-run must never reach this function
    from reliability_harness.runtime.generation.generator import generate_for_tasks
    from reliability_harness.runtime.generation.llm_client import LLMClient

    adapter = get_adapter(benchmark)
    tasks = adapter.load_tasks(limit=limit)
    llm_client = LLMClient.from_env(
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return generate_for_tasks(
        tasks=tasks,
        llm_client=llm_client,
        model_name=model_name,
        limit=None,
    )


def _execute_generation_artifact_entrypoint(
    path: str,
    use_docker: bool = True,
    timeout_ms: int = 10000,
) -> dict[str, Any]:
    """Execute a single per-task generation artifact (Benchmark-4C.2a).

    Deferred import ensures dry-run and generate modes never import
    execution helpers or trigger Docker-related imports.
    """
    from reliability_harness.runtime.execution.integration import execute_generation_artifact

    return execute_generation_artifact(
        generation_artifact_path=path,
        use_docker=use_docker,
        timeout_ms=timeout_ms,
    )


def _execute_aggregate_run_summaries_entrypoint(paths: list[str]) -> dict[str, Any]:
    """Aggregate multiple run summary JSON files into a single aggregate summary (Benchmark-6B.1).

    Deferred imports ensure dry-run, generate, and execute modes never import
    aggregate summary helpers.
    """
    from reliability_harness.artifacts.aggregate_summary import (
        build_aggregate_summary_from_paths,
        write_aggregate_summary,
    )

    summary = build_aggregate_summary_from_paths(paths)
    artifact_path = write_aggregate_summary(summary)
    return {
        "aggregate_summary_artifact_path": str(artifact_path),
        "summary_written": True,
        "input": summary["input"],
        "counts": summary["counts"],
        "rates": summary["rates"],
        "distributions": summary["distributions"],
        "artifact_version": summary.get("artifact_version"),
    }


def run(
    benchmark: str | None = None,
    dry_run_mode: bool = False,
    generate_mode: bool = False,
    execute_generation_artifact_path: str | None = None,
    aggregate_run_summary_paths: list[str] | None = None,
    execute_local: bool = False,
    execution_timeout_ms: int = 10000,
    **kwargs: Any,
) -> dict[str, Any]:
    """Main benchmark run entry point.

    Parameters
    ----------
    benchmark:
        Benchmark name, e.g. "mbpp", "humaneval", or "tiny".
        Required for dry_run_mode and generate_mode.
        Not required when execute_generation_artifact_path or aggregate_run_summary_paths is set.
    dry_run_mode:
        If True, return the pipeline manifest without loading data or calling LLMs.
    generate_mode:
        If True, run Benchmark-3 generation-only LLM candidate generation.
        Requires DEEPSEEK_API_KEY. Does not execute generated code.
    execute_generation_artifact_path:
        If set, execute a single per-task generation artifact JSON (Benchmark-4C.2a).
        Uses Docker by default; set execute_local=True for local runner.
        Does not call LLMClient, generator, memory, or retry.
    aggregate_run_summary_paths:
        If set, aggregate multiple run summary JSON files into a single aggregate
        summary artifact (Benchmark-6B.1). Does not call LLM, Docker, or execute code.
    execute_local:
        If True, use local runner (use_docker=False) for execution mode.
        Only safe for trusted fixture code.
    **kwargs:
        Options forwarded to generation mode: limit, model_name, temperature, max_tokens.

    Returns
    -------
    dict
        Dry-run manifest, generation manifest, execution summary, or future run summary.

    Raises
    ------
    ValueError
        When multiple mutually exclusive modes are active simultaneously.
    NotImplementedError
        When no mode flag is set (full execution not yet implemented).
    """
    # Mutual exclusion: --dry-run, --generate, --execute-generation-artifact, --aggregate-run-summaries
    active_modes = [
        ("--dry-run", dry_run_mode),
        ("--generate", generate_mode),
        ("--execute-generation-artifact", execute_generation_artifact_path is not None),
        ("--aggregate-run-summaries", aggregate_run_summary_paths is not None),
    ]
    active_names = [name for name, is_active in active_modes if is_active]
    if len(active_names) > 1:
        raise ValueError(
            f"Modes are mutually exclusive: {' and '.join(active_names)} cannot be combined."
        )

    if dry_run_mode:
        return dry_run(benchmark)

    if generate_mode:
        return _execute_generate(
            benchmark=benchmark,
            limit=kwargs.get("limit"),
            model_name=str(kwargs.get("model_name", "deepseek-chat")),
            temperature=float(kwargs.get("temperature", 0.0)),
            max_tokens=int(kwargs.get("max_tokens", 1024)),
        )

    if execute_generation_artifact_path is not None:
        return _execute_generation_artifact_entrypoint(
            path=execute_generation_artifact_path,
            use_docker=not execute_local,
            timeout_ms=execution_timeout_ms,
        )

    if aggregate_run_summary_paths is not None:
        return _execute_aggregate_run_summaries_entrypoint(aggregate_run_summary_paths)

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
            "Use --dry-run to validate the pipeline skeleton. "
            "Use --generate for Benchmark-3 generation-only LLM candidate generation. "
            "Use --execute-generation-artifact for Benchmark-4C.2a single-artifact execution."
        ),
    )
    parser.add_argument(
        "--benchmark",
        required=False,
        default=None,
        choices=list_benchmarks(),
        metavar="BENCHMARK",
        help=(
            f"Benchmark to run. Supported: {', '.join(list_benchmarks())}. "
            "Required for --dry-run and --generate. "
            "Optional when --execute-generation-artifact is used "
            "(benchmark is read from the artifact JSON)."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help=(
            "Print the pipeline skeleton manifest. Does not call LLMs, Docker, "
            "memory, or execute code. For fixture-backed benchmarks (tiny, mbpp, "
            "humaneval), writes a dry-run manifest to outputs/benchmark_results/."
        ),
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        default=False,
        help=(
            "Run Benchmark-3 generation-only LLM candidate generation. "
            "Requires DEEPSEEK_API_KEY in .env or environment. "
            "Does not execute generated code."
        ),
    )
    parser.add_argument(
        "--execute-generation-artifact",
        dest="execute_generation_artifact",
        default=None,
        metavar="PATH",
        help=(
            "Execute a single per-task generation artifact JSON (Benchmark-4C.2a). "
            "Input must be a per-task artifact produced by --generate. "
            "Default runner is Docker. Use --execute-local for local runner. "
            "Cannot be combined with --dry-run or --generate."
        ),
    )
    parser.add_argument(
        "--execute-local",
        dest="execute_local",
        action="store_true",
        default=False,
        help=(
            "Use local runner instead of Docker for --execute-generation-artifact. "
            "Only safe for trusted fixture code. Not for untrusted agent-generated code."
        ),
    )
    parser.add_argument(
        "--execution-timeout-ms",
        dest="execution_timeout_ms",
        type=int,
        default=10000,
        help=(
            "Docker execution timeout in milliseconds for --execute-generation-artifact "
            "(default: 10000). The default 10000ms accounts for Docker cold-start overhead; "
            "1000ms is too short and will cause spurious timeouts."
        ),
    )
    parser.add_argument(
        "--aggregate-run-summaries",
        dest="aggregate_run_summaries",
        nargs="+",
        default=None,
        metavar="PATH",
        help=(
            "Aggregate multiple run summary JSON files into a single aggregate summary artifact "
            "(Benchmark-6B.1). Accepts one or more explicit file paths; shell glob expansion is "
            "supported. Does not call LLM, Docker, or execute code. "
            "Cannot be combined with --dry-run, --generate, or --execute-generation-artifact."
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Limit generation to the first N tasks.",
    )
    parser.add_argument(
        "--model-name",
        dest="model_name",
        default="deepseek-chat",
        help="LLM model name (default: deepseek-chat).",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Sampling temperature (default: 0.0).",
    )
    parser.add_argument(
        "--max-tokens",
        dest="max_tokens",
        type=int,
        default=1024,
        help="Max tokens per generation (default: 1024).",
    )
    args = parser.parse_args(argv)

    # Mutual exclusion validation
    active = []
    if args.dry_run:
        active.append("--dry-run")
    if args.generate:
        active.append("--generate")
    if args.execute_generation_artifact is not None:
        active.append("--execute-generation-artifact")
    if args.aggregate_run_summaries is not None:
        active.append("--aggregate-run-summaries")
    if len(active) > 1:
        parser.error(
            f"Modes are mutually exclusive: {' and '.join(active)} cannot be combined."
        )

    # --benchmark required unless --execute-generation-artifact or --aggregate-run-summaries is used
    if (
        args.execute_generation_artifact is None
        and args.aggregate_run_summaries is None
        and args.benchmark is None
    ):
        parser.error(
            "--benchmark is required. Supported: "
            + ", ".join(list_benchmarks())
            + ". (--benchmark is optional only when --execute-generation-artifact "
            + "or --aggregate-run-summaries is used)"
        )

    result = run(
        benchmark=args.benchmark,
        dry_run_mode=args.dry_run,
        generate_mode=args.generate,
        execute_generation_artifact_path=args.execute_generation_artifact,
        aggregate_run_summary_paths=args.aggregate_run_summaries,
        execute_local=args.execute_local,
        execution_timeout_ms=args.execution_timeout_ms,
        limit=args.limit,
        model_name=args.model_name,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
