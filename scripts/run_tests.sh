#!/usr/bin/env bash
# Run ReliabilityHarness tests from any cwd.
# Transitional: ReActX/test_*.py tests are still in ReActX/ and run with ReActX/ in PYTHONPATH.
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
