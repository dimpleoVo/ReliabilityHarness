"""ReliabilityHarness package CLI.

Usage:
    python -m reliability_harness.cli info
    python -m reliability_harness.cli paths
    python -m reliability_harness.cli benchmark --benchmark mbpp --dry-run
    python -m reliability_harness.cli benchmark --benchmark humaneval --dry-run
    python -m reliability_harness.cli benchmark --benchmark tiny --generate --limit 1 --model-name deepseek-chat
    python -m reliability_harness.cli benchmark --execute-generation-artifact outputs/predictions/<run_id>/tiny_001.json
    python -m reliability_harness.cli benchmark --execute-generation-artifact <artifact> --execution-timeout-ms 10000
"""
import argparse
import json
import sys

from reliability_harness.utils.paths import (
    REPO_ROOT,
    PACKAGE_ROOT,
    CONFIGS_ROOT,
    DOCS_ROOT,
    SCRIPTS_ROOT,
    ARTIFACTS_ROOT,
    REPORTS_ROOT,
    get_pythonpath,
    get_docker_compose_file,
    get_backend_dockerfile,
    get_sandbox_dockerfile,
)


def cmd_info(_args: argparse.Namespace) -> None:
    info = {
        "project_name": "ReliabilityHarness",
        "package_name": "reliability_harness",
        "runtime_layer": "reliability_harness.runtime",
        "evaluation_layer": "reliability_harness.evaluation",
        "sandbox_layer": "reliability_harness.sandbox",
        "artifact_layer": "reliability_harness.artifacts",
        "reporting_layer": "reliability_harness.reporting",
    }
    for k, v in info.items():
        print(f"{k}: {v}")


def cmd_paths(_args: argparse.Namespace) -> None:
    paths = {
        "repo_root": REPO_ROOT,
        "package_root": PACKAGE_ROOT,
        "configs_root": CONFIGS_ROOT,
        "docs_root": DOCS_ROOT,
        "scripts_root": SCRIPTS_ROOT,
        "artifacts_root": ARTIFACTS_ROOT,
        "reports_root": REPORTS_ROOT,
        "docker_compose_file": get_docker_compose_file(),
        "backend_dockerfile": get_backend_dockerfile(),
        "sandbox_dockerfile": get_sandbox_dockerfile(),
        "pythonpath": get_pythonpath(),
    }
    for k, v in paths.items():
        print(f"{k}: {v}")


def cmd_benchmark(args: argparse.Namespace) -> None:
    from reliability_harness.experiments.run_benchmark import run

    result = run(
        benchmark=args.benchmark,
        dry_run_mode=args.dry_run,
        generate_mode=getattr(args, "generate", False),
        limit=getattr(args, "limit", None),
        model_name=getattr(args, "model_name", "deepseek-chat"),
        temperature=getattr(args, "temperature", 0.0),
        max_tokens=getattr(args, "max_tokens", 1024),
        execute_generation_artifact_path=getattr(args, "execute_generation_artifact", None),
        execute_local=getattr(args, "execute_local", False),
        execution_timeout_ms=getattr(args, "execution_timeout_ms", 10000),
    )
    print(json.dumps(result, indent=2))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m reliability_harness.cli",
        description="ReliabilityHarness package CLI",
    )
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("info", help="Show package layer info")
    sub.add_parser("paths", help="Show resolved filesystem paths")

    from reliability_harness.benchmarks.registry import list_benchmarks
    _benchmarks = list_benchmarks()
    bm = sub.add_parser(
        "benchmark",
        help="Run benchmark dry-run, generation, or execution artifact",
    )
    bm.add_argument(
        "--benchmark",
        required=False,
        default=None,
        choices=_benchmarks,
        metavar="BENCHMARK",
        help=(
            f"Benchmark name. Supported: {', '.join(_benchmarks)}. "
            "Required for --dry-run and --generate. "
            "Optional when --execute-generation-artifact is used "
            "(benchmark is read from the artifact JSON)."
        ),
    )
    bm.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print pipeline skeleton without loading data or running experiments",
    )
    bm.add_argument(
        "--generate",
        action="store_true",
        default=False,
        help="Run Benchmark-3 generation-only LLM candidate generation (requires DEEPSEEK_API_KEY)",
    )
    bm.add_argument(
        "--execute-generation-artifact",
        dest="execute_generation_artifact",
        default=None,
        metavar="PATH",
        help=(
            "Execute a single per-task generation artifact JSON (Benchmark-4C.2b). "
            "Input must be a per-task artifact produced by --generate. "
            "Default runner is Docker. Use --execute-local for local runner. "
            "Cannot be combined with --dry-run or --generate."
        ),
    )
    bm.add_argument(
        "--execute-local",
        dest="execute_local",
        action="store_true",
        default=False,
        help=(
            "Use local runner instead of Docker for --execute-generation-artifact. "
            "Only safe for trusted fixture code. Not for untrusted agent-generated code."
        ),
    )
    bm.add_argument(
        "--execution-timeout-ms",
        dest="execution_timeout_ms",
        type=int,
        default=10000,
        help=(
            "Docker execution timeout in milliseconds for --execute-generation-artifact "
            "(default: 10000). The default 10000ms accounts for Docker cold-start overhead."
        ),
    )
    bm.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Limit generation to the first N tasks",
    )
    bm.add_argument(
        "--model-name",
        dest="model_name",
        default="deepseek-chat",
        help="LLM model name for generation (default: deepseek-chat)",
    )
    bm.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Sampling temperature (default: 0.0)",
    )
    bm.add_argument(
        "--max-tokens",
        dest="max_tokens",
        type=int,
        default=1024,
        help="Max tokens per generation (default: 1024)",
    )

    args = parser.parse_args(argv)

    if args.command == "info":
        cmd_info(args)
    elif args.command == "paths":
        cmd_paths(args)
    elif args.command == "benchmark":
        # Mutual exclusion: --dry-run, --generate, --execute-generation-artifact
        active = []
        if args.dry_run:
            active.append("--dry-run")
        if args.generate:
            active.append("--generate")
        if args.execute_generation_artifact is not None:
            active.append("--execute-generation-artifact")
        if len(active) > 1:
            bm.error(
                f"Modes are mutually exclusive: {' and '.join(active)} cannot be combined."
            )
        # --benchmark required unless --execute-generation-artifact is set
        if args.execute_generation_artifact is None and args.benchmark is None:
            bm.error(
                "--benchmark is required. Supported: "
                + ", ".join(_benchmarks)
                + ". (--benchmark is optional only when --execute-generation-artifact is used)"
            )
        cmd_benchmark(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
