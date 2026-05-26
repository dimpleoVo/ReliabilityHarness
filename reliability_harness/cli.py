"""ReliabilityHarness package CLI.

Usage:
    python -m reliability_harness.cli info
    python -m reliability_harness.cli paths
    python -m reliability_harness.cli benchmark --benchmark mbpp --dry-run
    python -m reliability_harness.cli benchmark --benchmark humaneval --dry-run
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
    from reliability_harness.benchmarks.registry import list_benchmarks

    result = run(benchmark=args.benchmark, dry_run_mode=args.dry_run)
    print(json.dumps(result, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m reliability_harness.cli",
        description="ReliabilityHarness package CLI",
    )
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("info", help="Show package layer info")
    sub.add_parser("paths", help="Show resolved filesystem paths")

    from reliability_harness.benchmarks.registry import list_benchmarks
    bm = sub.add_parser("benchmark", help="Run benchmark dry-run skeleton")
    bm.add_argument(
        "--benchmark",
        required=True,
        choices=list_benchmarks(),
        metavar="BENCHMARK",
        help=f"Benchmark name. Supported: {', '.join(list_benchmarks())}",
    )
    bm.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print pipeline skeleton without loading data or running experiments",
    )

    args = parser.parse_args()

    if args.command == "info":
        cmd_info(args)
    elif args.command == "paths":
        cmd_paths(args)
    elif args.command == "benchmark":
        cmd_benchmark(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
