#!/usr/bin/env bash
# Official ReliabilityHarness test entrypoint.
# Runs root-level authoritative tests only. No ReActX legacy tests.
#
# Legacy ReActX tests are available only via:
#   bash scripts/legacy/run_reactx_tests.sh
#
# Usage (from any cwd):
#   bash scripts/run_tests.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

export PYTHONPATH="$REPO_ROOT"

cd "$REPO_ROOT"

echo "=== ReliabilityHarness root tests (authoritative) ==="
python -m pytest \
  tests/test_benchmark_entrypoint.py \
  tests/test_benchmark_registry.py \
  tests/test_benchmark_task_schema.py \
  tests/test_edit_distance_not_success_gate.py \
  tests/test_tiny_fixture_adapter.py \
  tests/test_mbpp_small_adapter.py \
  tests/test_humaneval_small_adapter.py \
  tests/test_generation_prompt_builder.py \
  tests/test_generation_code_extractor.py \
  tests/test_generation_artifact.py \
  tests/test_generation_mode.py \
  tests/test_execution_contract.py \
  tests/test_local_execution_runner.py \
  tests/test_execution_artifact.py \
  tests/test_docker_execution_runner.py \
  tests/test_execution_integration.py \
  tests/test_benchmark_execution_entrypoint.py \
  tests/test_benchmark_cli_forwarding.py \
  tests/test_run_summary_artifact.py \
  tests/test_process_metrics.py \
  tests/test_failure_diagnostics.py \
  tests/test_aggregate_summary.py \
  -v
