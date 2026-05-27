#!/usr/bin/env bash
# LEGACY — NOT the official ReliabilityHarness test entrypoint.
# This is a legacy compatibility script. It is not part of official ReliabilityHarness experiments.
#
# WARNING: This is a legacy ReActX test runner.
# It is NOT part of the official ReliabilityHarness paper test path.
# legacy/ReActX/test_*.py tests are NOT constraints on the reliability_harness architecture.
#
# Official ReliabilityHarness test entrypoint:
#   bash scripts/run_tests.sh
#
# Use this script only for manual legacy smoke checks of the archived ReActX layer.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo ""
echo "================================================================"
echo "  WARNING: Legacy ReActX test runner (archived)"
echo "  This is a legacy compatibility script."
echo "  It is NOT part of official ReliabilityHarness experiments."
echo "  legacy/ReActX/test_*.py are NOT constraints on the new architecture."
echo "  Official tests: bash scripts/run_tests.sh"
echo "================================================================"
echo ""

# legacy/ReActX tests require both repo root and legacy/ReActX/ on PYTHONPATH
# so that reliability_harness.* and legacy/ReActX/utils.* imports both resolve.
export PYTHONPATH="$REPO_ROOT:$REPO_ROOT/legacy/ReActX"

# Run from legacy/ReActX/ so that internal utils.* relative imports resolve correctly.
cd "$REPO_ROOT/legacy/ReActX"
python run_tests.py
