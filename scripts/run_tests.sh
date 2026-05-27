#!/usr/bin/env bash
# Run ReliabilityHarness tests from any cwd.
#
# New paper benchmark entrypoint (dry-run validation):
#   bash scripts/run_benchmark_dry_run.sh mbpp
#   python -m reliability_harness.experiments.run_benchmark --benchmark mbpp --dry-run
#
# New root-level tests (Migration-4A/B, authoritative for new architecture):
#   python -m pytest tests/test_benchmark_entrypoint.py tests/test_benchmark_registry.py tests/test_benchmark_task_schema.py
#
# NOTE: ReActX/test_*.py tests below are LEGACY / TRANSITIONAL.
# They are NOT constraints on the new reliability_harness architecture.
# They run against the old ReActX/app/* shim layer and will be retired in Migration-3.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# repo root on PYTHONPATH covers both reliability_harness.* and shim app/evalforge
export PYTHONPATH="$REPO_ROOT:$REPO_ROOT/ReActX"

echo "=== pytest tests/ ==="
python -m pytest "$REPO_ROOT/tests" -v

echo ""
echo "=== ReActX transitional tests (python run_tests.py) ==="
# Still run from ReActX/ so internal utils.* imports resolve
cd "$REPO_ROOT/ReActX"
python run_tests.py
