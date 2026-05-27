#!/usr/bin/env bash
# Official ReliabilityHarness dry-run benchmark script.
# This is the NEW paper benchmark entrypoint for shell usage.
# Does NOT use ReActX / run_eval.py / EvalForge. No LLM calls. No data loading.
# No Docker. No output writes.
#
# Usage (from any cwd):
#   bash scripts/run_benchmark_dry_run.sh            # default: mbpp
#   bash scripts/run_benchmark_dry_run.sh mbpp
#   bash scripts/run_benchmark_dry_run.sh humaneval
#
# Equivalent Python invocation:
#   python -m reliability_harness.experiments.run_benchmark --benchmark mbpp --dry-run
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

BENCHMARK="${1:-mbpp}"

export PYTHONPATH="$REPO_ROOT"

cd "$REPO_ROOT"

python -m reliability_harness.experiments.run_benchmark --benchmark "$BENCHMARK" --dry-run
