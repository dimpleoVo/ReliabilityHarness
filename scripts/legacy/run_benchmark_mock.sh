#!/usr/bin/env bash
# LEGACY — NOT the paper benchmark entrypoint.
# Legacy mock benchmark runner. Not part of official ReliabilityHarness paper benchmark path.
# This script invokes run_eval.py (EvalForge-era); do not use for paper results.
#
# Official paper benchmark entrypoint:
#   bash scripts/run_benchmark_dry_run.sh mbpp
#   python -m reliability_harness.experiments.run_benchmark --benchmark mbpp --dry-run
#
# This file is preserved for historical reference only.
# Run a mock benchmark eval (no real LLM, no real sandbox).
# Works from any cwd.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

export PYTHONPATH="$REPO_ROOT:$REPO_ROOT/ReActX"
export BENCHMARK_MOCK=1

python "$REPO_ROOT/run_eval.py" --config "$REPO_ROOT/configs/benchmark_eval.yaml"
