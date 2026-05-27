#!/usr/bin/env bash
# LEGACY — NOT the paper benchmark entrypoint.
# This is a legacy compatibility script. It is not part of official ReliabilityHarness experiments.
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

echo ""
echo "================================================================"
echo "  WARNING: Legacy mock benchmark runner (archived)"
echo "  This is a legacy compatibility script."
echo "  It is NOT part of official ReliabilityHarness experiments."
echo "  Official benchmark: bash scripts/run_benchmark_dry_run.sh mbpp"
echo "================================================================"
echo ""

export PYTHONPATH="$REPO_ROOT:$REPO_ROOT/legacy/ReActX"
export BENCHMARK_MOCK=1

python "$REPO_ROOT/run_eval.py" --config "$REPO_ROOT/configs/benchmark_eval.yaml"
