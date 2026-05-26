#!/usr/bin/env bash
# Show ReliabilityHarness resolved paths.
# Works from any cwd.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

export PYTHONPATH="$REPO_ROOT"
python -m reliability_harness.cli paths
