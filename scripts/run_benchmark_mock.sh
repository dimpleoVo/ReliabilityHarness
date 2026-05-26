#!/usr/bin/env bash
# Transitional legacy mock script. New paper benchmarks use:
#   python -m reliability_harness.experiments.run_benchmark --benchmark <name> --dry-run
# This script invokes run_eval.py (EvalForge-era); do not use for paper results.
# Run a mock benchmark eval (no real LLM, no real sandbox).
# Works from any cwd.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

export PYTHONPATH="$REPO_ROOT:$REPO_ROOT/ReActX"
export BENCHMARK_MOCK=1

python "$REPO_ROOT/run_eval.py" --config "$REPO_ROOT/configs/benchmark_eval.yaml"
