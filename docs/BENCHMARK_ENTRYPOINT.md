# ReliabilityHarness — Benchmark Entrypoint Reference

> **Migration-5A status:** `ReActX/`, `app/`, and `evalforge/` have been archived to `legacy/`.
> Root-level `tests/` are the authoritative test constraints for the new architecture.
> `legacy/ReActX/test_*.py` are archived legacy tests and are NOT constraints on `reliability_harness.*`.

## Formal Paper Experiment Entrypoints

The sole authoritative entrypoints for ReliabilityHarness paper experiments are:

**Shell (recommended):**
```bash
bash scripts/run_benchmark_dry_run.sh tiny        # Benchmark-1: tiny fixture (writes artifact)
bash scripts/run_benchmark_dry_run.sh mbpp
bash scripts/run_benchmark_dry_run.sh humaneval
```

**Python module:**
```bash
python -m reliability_harness.experiments.run_benchmark --benchmark <name> [--dry-run]
```

Supported benchmarks: `tiny`, `mbpp`, `humaneval`

> **Current phase (Benchmark-3):** `--generate` mode is now available for LLM candidate
> generation (no code execution, no Docker, no pass/fail evaluation). Full process-aware
> execution (agent runtime, sandbox, metrics) will be enabled in a future benchmark phase.

---

## Benchmark-6A: Aggregate Summary over Run Summaries

**Status:** Implemented.

**Scope:** `build_aggregate_summary()` aggregates a list of per-task run summary dicts
into a single machine-readable aggregate summary for paper tables and experiment statistics.

**Computed fields:**

| Field | Location | Definition |
|---|---|---|
| `final_success_rate` | `rates` | fraction of runs where `success.final_success` is `true` |
| `observable_process_success_rate` | `rates` | fraction where `metrics.process.observable_process_success` is `true` |
| `failure_observed_rate` | `rates` | fraction where `diagnostics.failure.failure_observed` is `true` |
| `timeout_rate` | `rates` | fraction where `metrics.process.timeout_observed` is `true` |
| `runtime_error_rate` | `rates` | fraction where `metrics.process.runtime_error_observed` is `true` |
| `failure_stage_distribution` | `distributions` | count by `diagnostics.failure.failure_stage` |
| `failure_type_distribution` | `distributions` | count by `diagnostics.failure.failure_type` |

**Important semantics:**
- `final_success_rate` is the fraction of runs where final execution succeeded.  
  It is **not** a full reliability score.
- `observable_process_success_rate` is based only on minimal observable artifact fields (Benchmark-5A).  
  It is **not** full process correctness.
- Distributions are raw counts, not fractions.
- `total_runs == 0` → all rates are `0.0` (no divide-by-zero error).

**New module:** `reliability_harness/artifacts/aggregate_summary.py`

**Public API:**
```python
from reliability_harness.artifacts.aggregate_summary import (
    build_aggregate_summary,            # from a list of run summary dicts
    build_aggregate_summary_from_paths, # load from disk + aggregate
    write_aggregate_summary,            # write to outputs/artifacts/aggregate_summaries/
    load_json,                          # load JSON (raises AggregateSummaryError)
    AggregateSummaryError,              # raised on missing/invalid input
)
```

**Output path:** `outputs/artifacts/aggregate_summaries/aggregate_summary_{timestamp}.json`  
(covered by `.gitignore` via `outputs/*`).

**What is NOT implemented (Benchmark-6A boundaries):**
- batch execution, code generation
- retry / recovery metrics
- memory metrics
- reasoning consistency, tool correctness
- LLM-as-judge, full failure taxonomy
- report generation

Aggregate summary does **not** execute code, call LLM, or use Docker.
It reads only pre-computed run summary artifact fields.

**Benchmark-6A boundaries:**
- `run_benchmark.py` and `cli.py` are unchanged.
- No batch, manifest, or directory processing.
- No generate+execute+summarize one-command pipeline changes.

---

## Benchmark-6B.1: run_benchmark Aggregate Summary Entrypoint

**Status:** Implemented.

**Scope:** `run_benchmark.py` now supports `--aggregate-run-summaries` for aggregating
multiple pre-computed run summary artifacts into a single aggregate summary.
Wires the `--aggregate-run-summaries` flag to `build_aggregate_summary_from_paths()`
and `write_aggregate_summary()` from Benchmark-6A.  
**Not in scope:** CLI forwarding (`cli.py` unchanged), directory/manifest/glob processing
inside Python, batch execution, code generation.

**Target command:**
```bash
python -m reliability_harness.experiments.run_benchmark \
  --aggregate-run-summaries outputs/artifacts/run_summaries/*.json
```

Shell glob expansion (`*.json`) is supported. Python-internal glob, directory
recursion, and manifest files are NOT supported — paths must be explicit.

**What this entrypoint does NOT do:**
- Does not call LLM or require an API key
- Does not call Docker or execute any code
- Does not run generation, execution, or retry
- Does not perform directory scanning or manifest resolution

**Output path:** `outputs/artifacts/aggregate_summaries/aggregate_summary_{timestamp}.json`  
(covered by `.gitignore` via `outputs/*`).

**Returned JSON fields:**

| Field | Description |
|---|---|
| `aggregate_summary_artifact_path` | Path of the written aggregate summary JSON |
| `summary_written` | Always `true` on success |
| `input` | `{ "run_summary_paths": [...] }` |
| `counts` | `total_runs`, `final_success_count`, etc. |
| `rates` | `final_success_rate`, `observable_process_success_rate`, etc. |
| `distributions` | `failure_stage_distribution`, `failure_type_distribution` |
| `artifact_version` | Forwarded from the aggregate summary (e.g. `"6A.1"`) |

**Mode mutual exclusion (updated):**

| Combination | Result |
|---|---|
| `--aggregate-run-summaries` alone | OK |
| `--aggregate-run-summaries` without `--benchmark` | OK |
| `--aggregate-run-summaries --benchmark tiny` | OK (benchmark is unused) |
| `--aggregate-run-summaries --dry-run` | Error: mutually exclusive |
| `--aggregate-run-summaries --generate` | Error: mutually exclusive |
| `--aggregate-run-summaries --execute-generation-artifact` | Error: mutually exclusive |
| `--dry-run` without `--benchmark` | Error: --benchmark required |
| `--generate` without `--benchmark` | Error: --benchmark required |

**Benchmark-6B.1 boundaries:**
- `cli.py` is unchanged — CLI forwarding is not implemented yet.
- Input must be explicit run summary JSON paths (shell-expanded by the shell).
- No batch, manifest, directory, or Python-internal glob processing.
- No generate+execute+summarize one-command pipeline.
- No LLM calls, no Docker, no retry/memory.
- Aggregate summary output goes to `outputs/artifacts/aggregate_summaries/`.

---

## Benchmark-5B: Minimal Observable Failure Diagnostics

**Status:** Implemented.

**Scope:** `build_run_summary()` now automatically populates `diagnostics.failure` with
minimal observable failure diagnostic signals derived from generation and execution artifact fields.

**Fields populated in `diagnostics.failure`:**

| Field | Type | Definition |
|---|---|---|
| `failure_observed` | `bool` | `true` if any failure was detected |
| `failure_stage` | `str` | `"none"` / `"extraction"` / `"execution"` / `"unknown"` |
| `failure_type` | `str` | see enum below |
| `failure_source` | `str \| null` | artifact field that triggered the diagnosis |
| `timed_out` | `bool` | `timed_out` value from execution section |
| `error_type` | `str \| null` | `error_type` value from execution section |
| `is_full_failure_taxonomy` | `bool` | always `false` |
| `definition` | `str` | human-readable definition string |

**`failure_stage` enum:**

| Value | Condition |
|---|---|
| `"none"` | no failure observed |
| `"extraction"` | `extraction_status != "success"` OR `has_extracted_code is False` |
| `"execution"` | extraction succeeded but execution failed |
| `"unknown"` | required fields missing or section absent |

Note: `diagnostics.failure` does not use `"completed"` — it describes the stage of failure,
not a pipeline completion state.  When `metrics.process.process_failure_stage == "completed"`,
`diagnostics.failure.failure_stage` is `"none"`.

**`failure_type` enum (priority order):**

| Value | Trigger |
|---|---|
| `"extraction_failed"` | `extraction_status != "success"` |
| `"no_extracted_code"` | `extraction_status == "success"` AND `has_extracted_code is False` |
| `"execution_not_performed"` | extraction succeeded AND `execution_performed is not True` |
| `"timeout"` | `timed_out is True` |
| `"assertion_failure"` | `error_type == "assertion_failure"` |
| `"syntax_error"` | `error_type == "syntax_error"` |
| `"runtime_error"` | `error_type == "runtime_error"` |
| `"unknown_execution_error"` | `tests_passed is False` AND `error_type` is unrecognised/None |
| `"none"` | success |
| `"unknown"` | required fields missing |

**`diagnostics.failure` is auto-populated in `build_run_summary()`.** No API change required.
`metrics.process`, `metrics.recovery`, `metrics.memory` are unchanged.

**What is NOT implemented (Benchmark-5B boundaries):**
- root-cause analysis
- LLM-as-judge
- reasoning trace
- tool correctness
- retry / recovery
- memory-assisted recovery
- full failure taxonomy

These are minimal observable diagnostics, **not full root-cause taxonomy**.

**New module:** `reliability_harness/diagnostics/failure_diagnostics.py`

**Public API:**
```python
from reliability_harness.diagnostics.failure_diagnostics import (
    compute_minimal_failure_diagnostics,               # from a full summary dict
    compute_minimal_failure_diagnostics_from_sections, # from generation + execution section dicts
)
```

**Benchmark-5B boundaries:**
- `run_benchmark.py` and `cli.py` are unchanged.
- No batch, manifest, or directory processing.
- No generate+execute+summarize one-command pipeline changes.
- No LLM calls, no Docker, no retry/memory.

---

## Benchmark-5A: Minimal Observable Process Metrics

**Status:** Implemented.

**Scope:** `build_run_summary()` now automatically populates `metrics.process` with
minimal observable process signals derived from generation and execution artifact fields.

**Fields populated in `metrics.process`:**

| Field | Type | Definition |
|---|---|---|
| `generation_completed` | `bool` | `extraction_status` field is present in generation section |
| `code_extraction_success` | `bool` | `extraction_status == "success"` AND `has_extracted_code is True` |
| `execution_attempted` | `bool` | `execution_performed is True` |
| `execution_completed` | `bool` | `execution_performed is True` AND `timed_out is False` |
| `execution_success` | `bool` | `tests_passed is True` AND `timed_out is False` AND `error_type is None` |
| `timeout_observed` | `bool` | `timed_out is True` |
| `runtime_error_observed` | `bool` | `error_type == "runtime_error"` |
| `process_failure_stage` | `str` | `"extraction"` / `"execution"` / `"completed"` / `"unknown"` |
| `observable_process_success` | `bool` | all pipeline stages succeeded |
| `is_full_process_reliability_metric` | `bool` | always `false` |
| `definition` | `str` | human-readable definition string |

**`process_failure_stage` enum:**

| Value | Condition |
|---|---|
| `"extraction"` | `code_extraction_success is False` |
| `"execution"` | extraction succeeded but `execution_success is False` |
| `"completed"` | extraction succeeded AND execution succeeded |
| `"generation"` | reserved — future missing generation artifact / batch pipeline |
| `"unknown"` | required fields missing or generation section absent |

**`observable_process_success` definition:**
```
generation_completed
AND code_extraction_success
AND execution_attempted
AND execution_completed
AND execution_success
```

**Relation to `final_success`:**

`observable_process_success` may align with `final_success` in simple single-attempt
code-generation tasks. They are semantically different:

- `final_success` — final execution success proxy  
  (`extraction_status == success AND execution_performed AND tests_passed`)
- `observable_process_success` — minimal observable pipeline success signal

`observable_process_success` is **not** a replacement for future reasoning/tool/retry/memory
metrics. `is_full_process_reliability_metric` is always `false`.

**What is NOT implemented (Benchmark-5A boundaries):**
- reasoning consistency
- tool correctness
- retry / recovery
- memory-assisted recovery
- LLM-as-judge
- full failure taxonomy

These are minimal observable process signals, **not full process reliability metrics**.

**New module:** `reliability_harness/metrics/process_metrics.py`

**Public API:**
```python
from reliability_harness.metrics.process_metrics import (
    compute_minimal_process_metrics,               # from a full summary dict
    compute_minimal_process_metrics_from_sections, # from generation + execution section dicts
)
```

**`metrics.process` is auto-populated in `build_run_summary()`.** No API change required.
`metrics.recovery` and `metrics.memory` remain empty extension points.
`diagnostics.failure` was empty at Benchmark-5A; it is now automatically populated by **Benchmark-5B**.

**Benchmark-5A boundaries:**
- `run_benchmark.py` and `cli.py` are unchanged.
- No batch, manifest, or directory processing.
- No generate+execute+summarize one-command pipeline changes.
- No LLM calls, no Docker, no retry/memory.

---

## Benchmark-4D.2: Auto Write Run Summary after Execution Artifact

**Status:** Implemented.

**Scope:** `execute_generation_artifact()` now auto-builds and writes a run summary artifact
immediately after writing the execution artifact. Both the module entrypoint
(`python -m reliability_harness.experiments.run_benchmark --execute-generation-artifact`)
and the CLI (`python -m reliability_harness.cli benchmark --execute-generation-artifact`)
return the new summary fields automatically.

**Full chain (Benchmark-4D.2):**
```
generation artifact (JSON)
  -> execution artifact  (outputs/executions/{run_id}/)
  -> run summary artifact  (outputs/artifacts/run_summaries/)
```

**New return fields:**

| Field | Type | Description |
|---|---|---|
| `run_summary_artifact_path` | `str \| null` | Path of written run summary JSON (`null` if `write_summary=False`) |
| `final_success` | `bool` | `extraction_status == success AND execution_performed AND tests_passed` |
| `summary_written` | `bool` | `true` if run summary was written, `false` if disabled |

**`final_success` definition:**
```
extraction_status == "success"
AND execution_performed is True
AND tests_passed is True
```
`final_success` is a **final execution success proxy**, NOT a process reliability metric.

**Example output (execution mode):**
```json
{
  "generation_artifact_path": "outputs/predictions/.../tiny_001.json",
  "execution_artifact_path": "outputs/executions/.../..._tiny_001.json",
  "run_summary_artifact_path": "outputs/artifacts/run_summaries/..._tiny_001_summary.json",
  "run_id": "...",
  "benchmark": "tiny",
  "task_id": "tiny_001",
  "model_name": "deepseek-v4-flash",
  "extraction_status": "success",
  "runner_type": "docker",
  "docker_used": true,
  "execution_performed": true,
  "tests_passed": true,
  "error_type": null,
  "final_success": true,
  "summary_written": true
}
```

**Run summary output path:** `outputs/artifacts/run_summaries/{run_id}_{task_id}_summary.json`
(covered by `.gitignore` via `outputs/*`).

**API change:**
```python
execute_generation_artifact(
    generation_artifact_path,
    *,
    output_root=None,
    backend=None,
    use_docker=True,
    timeout_ms=10000,
    write_summary=True,        # NEW — default True: auto-write run summary
    summary_output_dir=None,   # NEW — default: outputs/artifacts/run_summaries/
)
```

**Benchmark-4D.2 boundaries:**
- Summary is written by default (`write_summary=True`).
  Pass `write_summary=False` to disable (e.g. for testing).
- No batch, manifest, or directory summary.
- No generate+execute+summarize one-command pipeline.
- No process metrics, retry/recovery metrics, memory effect metrics.
- No failure taxonomy.
- `run_benchmark.py` and `cli.py` argument lists are **unchanged** —
  `write_summary` and `summary_output_dir` are only available via Python API.

---

## Benchmark-4D.1: Extensible Single-Run Summary Schema

**Status:** Implemented.

**Scope:** `reliability_harness/artifacts/run_summary.py` provides a run summary builder
that aggregates a generation artifact and its corresponding execution artifact into a
lightweight, machine-readable single-run summary.  
**Not in scope:** CLI / run_benchmark wiring, batch/manifest/directory summary, process metrics,
failure taxonomy, retry, memory effect.

| Component | File | Status |
|---|---|---|
| Run summary builder | `reliability_harness/artifacts/run_summary.py` | Done |
| Run summary tests | `tests/test_run_summary_artifact.py` | Done |

**Design: stable envelope + extensible sections**

```json
{
  "artifact_version": "4D.1",
  "created_at": "...",
  "identity":       { "run_id", "benchmark", "task_id", "model_name" },
  "artifact_refs":  { "generation_artifact_path", "execution_artifact_path" },
  "generation":     { "extraction_status", "has_extracted_code" },
  "execution":      { "execution_performed", "runner_type", "docker_used",
                      "tests_passed", "error_type", "timed_out", "execution_time_ms" },
  "success":        { "final_success", "definition", "is_process_reliability_metric" },
  "metrics":        { "process": {}, "recovery": {}, "memory": {} },
  "diagnostics":    { "failure": {} },
  "limitations":    [ "..." ]
}
```

**`final_success` definition:**

```
extraction_status == "success"
AND execution_performed is True
AND tests_passed is True
```

`final_success` is a **final execution success proxy**, not a process reliability metric.
`success.is_process_reliability_metric` is always `false`.
`metrics.process`, `metrics.recovery`, `metrics.memory`, and `diagnostics.failure` are
extension points — they are empty in Benchmark-4D.1 and populated by later benchmarks
(`metrics.process` by 5A, `diagnostics.failure` by 5B).

This distinction is fundamental to the paper thesis:
> *Final task success does not fully reflect agent reliability.*

**What the summary does NOT copy:**

Large raw fields — `prompt`, `raw_response`, `extracted_code`, `candidate_code`,
`stdout`, `stderr` — are never copied into the summary. Only path references to
the source artifacts are stored (`artifact_refs`).

**Public API:**

```python
from reliability_harness.artifacts.run_summary import (
    build_run_summary,               # main builder
    build_run_summary_from_paths,    # convenience: load from disk + build
    write_run_summary,               # write to outputs/artifacts/run_summaries/
    load_json,                       # load artifact JSON (raises RunSummaryError)
    RunSummaryError,                 # raised on missing/inconsistent fields
)
```

**Output path:** `outputs/artifacts/run_summaries/{run_id}_{task_id}_summary.json`
(covered by `.gitignore` via `outputs/*`).

**Benchmark-4D.1 boundaries:**
- `run_benchmark.py` and `cli.py` are **unchanged** — no wiring yet.
- Input must be a single (generation artifact, execution artifact) pair.
- No batch, manifest, or directory summary.
- No generate+execute+summarize one-command pipeline.
- No process metrics, retry/recovery metrics, memory effect metrics.
- No failure taxonomy.

---

## Benchmark-4C.2b: CLI Forwarding for Execution Artifact Mode

**Status:** Implemented.

**Scope:** `cli.py benchmark` subcommand now forwards `--execute-generation-artifact`,
`--execute-local`, and `--execution-timeout-ms` to `run_benchmark.run()`.
The CLI command is now equivalent to the module command for execution artifact mode.  
**Not in scope:** directory/manifest/batch execution, generate+execute one-command pipeline,
retry, memory, process reliability metrics.

| Component | File | Status |
|---|---|---|
| CLI forwarding | `reliability_harness/cli.py` | Done |
| CLI forwarding tests | `tests/test_benchmark_cli_forwarding.py` | Done |

**Target commands:**

```bash
# Execute a generation artifact via CLI (equivalent to python -m ...run_benchmark)
python -m reliability_harness.cli benchmark \
  --execute-generation-artifact outputs/predictions/<run_id>/tiny_001.json

# With explicit timeout
python -m reliability_harness.cli benchmark \
  --execute-generation-artifact outputs/predictions/<run_id>/tiny_001.json \
  --execution-timeout-ms 10000

# With local runner (trusted fixture code only, no Docker daemon required)
python -m reliability_harness.cli benchmark \
  --execute-generation-artifact outputs/predictions/<run_id>/tiny_001.json \
  --execute-local

# With explicit --benchmark (optional, for documentation; artifact JSON has benchmark)
python -m reliability_harness.cli benchmark \
  --benchmark tiny \
  --execute-generation-artifact outputs/predictions/<run_id>/tiny_001.json

# Existing modes unchanged
python -m reliability_harness.cli benchmark --benchmark tiny --dry-run
python -m reliability_harness.cli benchmark --benchmark tiny --generate --limit 1
```

**CLI ≡ module command:** The following pairs are equivalent:

```bash
python -m reliability_harness.cli benchmark \
  --execute-generation-artifact <artifact> --execution-timeout-ms 10000

python -m reliability_harness.experiments.run_benchmark \
  --execute-generation-artifact <artifact> --execution-timeout-ms 10000
```

**Benchmark-4C.2b boundaries:**

- `--execute-generation-artifact` is mutually exclusive with `--dry-run` and `--generate`.
- `--benchmark` is optional when `--execute-generation-artifact` is provided; required otherwise.
- Default runner is Docker (`--execute-local` not set). `--execute-local` overrides to local runner.
  Local runner is only safe for trusted fixture code — never for untrusted agent-generated code.
- Default Docker execution timeout is **10000ms** (`--execution-timeout-ms 10000`).
  1000ms is too short for Docker cold start and causes spurious `timed_out: true` results.
- No manifest execution, no directory execution, no batch execution.
- No generate+execute one-command pipeline.
- No retry, memory, or process reliability metrics.
- Execution artifacts are written to `outputs/executions/` (covered by `.gitignore`).

**Timeout flag:**

| Flag | Default | Notes |
|---|---|---|
| `--execution-timeout-ms N` | `10000` | Docker execution timeout per task. 1000ms causes cold-start timeouts. |

**Mode mutual exclusion (CLI layer):**

| Combination | Result |
|---|---|
| `--execute-generation-artifact` alone | OK |
| `--benchmark tiny --execute-generation-artifact` | OK |
| `--execute-generation-artifact --execute-local` | OK (local runner) |
| `--dry-run --execute-generation-artifact` | Error: mutually exclusive |
| `--generate --execute-generation-artifact` | Error: mutually exclusive |
| `--dry-run` without `--benchmark` | Error: --benchmark required |
| `--generate` without `--benchmark` | Error: --benchmark required |

---

## Benchmark-4C.2a: run_benchmark Execution Entrypoint

**Status:** Implemented.

**Scope:** `run_benchmark.py` now supports `--execute-generation-artifact` for single per-task
generation artifact execution. Wires the `--execute-generation-artifact` flag to
`execute_generation_artifact()` from Benchmark-4C.1.  
**Not in scope:** CLI forwarding (`cli.py` unchanged — Benchmark-4C.2b), directory/manifest/batch
execution, generate+execute one-command pipeline, retry, memory, process metrics.

| Component | File | Status |
|---|---|---|
| Execution entrypoint | `reliability_harness/experiments/run_benchmark.py` | Done |
| Entrypoint tests | `tests/test_benchmark_execution_entrypoint.py` | Done |

**Target commands:**

```bash
# Without --benchmark (benchmark is read from the artifact JSON)
python -m reliability_harness.experiments.run_benchmark \
  --execute-generation-artifact outputs/predictions/<run_id>/tiny_001.json

# With explicit timeout (default 10000ms covers Docker cold-start; 1000ms is too short)
python -m reliability_harness.experiments.run_benchmark \
  --execute-generation-artifact outputs/predictions/<run_id>/tiny_001.json \
  --execution-timeout-ms 10000

# With --benchmark (optional, for explicitness)
python -m reliability_harness.experiments.run_benchmark \
  --benchmark tiny \
  --execute-generation-artifact outputs/predictions/<run_id>/tiny_001.json

# Use local runner (trusted fixture code only, no Docker daemon required)
python -m reliability_harness.experiments.run_benchmark \
  --execute-generation-artifact outputs/predictions/<run_id>/tiny_001.json \
  --execute-local
```

**Benchmark-4C.2a boundaries:**
- Input must be a single per-task generation artifact JSON (produced by `--generate`).
- Default runner is Docker (`use_docker=True`). `--execute-local` overrides to local runner.
  Local runner is only safe for trusted fixture code.
- Default Docker execution timeout is **10000ms** (`--execution-timeout-ms 10000`).
  The `ExecutionInput` contract default of 1000ms is too short for Docker cold start and will
  cause spurious `timed_out: true` results. Always use ≥ 5000ms for Docker.
- `--execute-generation-artifact` is mutually exclusive with `--dry-run` and `--generate`.
- No directory execution, no manifest/batch execution, no generate+execute pipeline.
- No retry, memory, or process reliability metrics.
- `cli.py` is unchanged — CLI forwarding is Benchmark-4C.2b.
- Execution artifacts are written to `outputs/executions/` (covered by `.gitignore`).

**Timeout flag:**

| Flag | Default | Notes |
|---|---|---|
| `--execution-timeout-ms N` | `10000` | Docker execution timeout per task. 1000ms causes cold-start timeouts. |

**Mode mutual exclusion:**

| Combination | Result |
|---|---|
| `--execute-generation-artifact` alone | OK |
| `--benchmark tiny --execute-generation-artifact` | OK |
| `--execute-generation-artifact --execute-local` | OK (local runner) |
| `--dry-run --execute-generation-artifact` | Error: mutually exclusive |
| `--generate --execute-generation-artifact` | Error: mutually exclusive |

---

## Benchmark-4C.1: Generation-to-Execution Integration Helper

**Status:** Benchmark-4C.1 implemented (integration helper only — no CLI wiring).

**Scope:** `execute_generation_artifact()` connects a Benchmark-3 per-task generation artifact to the Benchmark-4 execution contract.  
**Not in scope:** `run_benchmark --execute`, CLI integration, retry, memory, process metrics.

| Component | File | Status |
|---|---|---|
| Integration helper | `reliability_harness/runtime/execution/integration.py` | Done |
| Unit tests (fake backend) | `tests/test_execution_integration.py` | Done |

**Data flow:**
```
generation artifact (JSON)
  -> extracted_code + BenchmarkTask.tests (via adapter)
  -> ExecutionInput
  -> execute_in_docker (fake backend in tests) or execute_locally
  -> ExecutionResult
  -> ExecutionArtifact -> outputs/executions/{run_id}/
```

**Benchmark-4C.1 boundaries:**
- `run_benchmark.py` and `cli.py` are **unchanged** — no `--execute` flag yet.
- Default tests use fake Docker backend — no Docker daemon required.
- Real Docker execution is validated in Benchmark-4B.2 smoke test (separate).
- No retry, memory, or process reliability metrics.
- `use_docker=False` path calls `execute_locally` — only safe for trusted fixture code.

**Exception:** `ExecutionIntegrationError` is raised for:
- Unreadable artifact JSON
- `extraction_status != "success"`
- `extracted_code` missing or empty
- `benchmark` or `task_id` missing
- `task_id` not found in benchmark adapter

**Summary dict keys:**
`generation_artifact_path`, `execution_artifact_path`, `run_id`, `benchmark`, `task_id`, `model_name`, `extraction_status`, `runner_type`, `docker_used`, `execution_performed`, `tests_passed`, `error_type`.

---

## Benchmark-4B: Docker Execution Runner

**Status:** Benchmark-4B.1 implemented (Docker runner schema adapter, mock backend tests only).

**Scope:** `execute_in_docker()` + `DockerExecutionBackend` protocol + `DockerBackendResult`.  
**Not in scope:** `run_benchmark --execute-docker` CLI flag, retry, memory, process metrics.

| Component | File | Status |
|---|---|---|
| Docker runner | `reliability_harness/runtime/execution/docker_runner.py` | Done |
| Unit tests (mock backend) | `tests/test_docker_execution_runner.py` | Done |
| Integration tests (real Docker) | `tests/test_docker_execution_runner_integration.py` | Optional / `@pytest.mark.docker` |

**Benchmark-4B.1 boundaries:**
- Default `scripts/run_tests.sh` uses a **fake backend** — no Docker daemon required.
- Real Docker smoke test exists at `tests/test_docker_execution_runner_integration.py` (marked `@pytest.mark.docker`, excluded from default run).
- `run_benchmark.py` and `cli.py` are **unchanged** — no `--execute-docker` flag yet.
- No retry, no memory, no process reliability metrics in this phase.
- Docker `python:3.11-slim` image, `--network none`, 128 MB memory limit, 0.5 CPU cap.

**Error type mapping:**

| Condition | `error_type` |
|---|---|
| `exit_code == 0` | `null` |
| `stderr` contains `AssertionError` | `assertion_failure` |
| `stderr` contains `SyntaxError` | `syntax_error` |
| `timed_out == True` | `timeout` |
| Other non-zero exit | `runtime_error` |
| Backend raises exception | `infrastructure_error` |

**Run integration tests manually:**
```bash
pytest -m docker tests/test_docker_execution_runner_integration.py -v
```

---

## Benchmark-4A: Execution Contract and Local Deterministic Runner

**Status:** Benchmark-4A.1 implemented (local deterministic execution contract only).

**Scope:** `ExecutionInput` / `ExecutionResult` contract + `execute_locally()` runner.  
**Not in scope:** Docker, real LLM-generated artifact execution, retry, memory, process metrics.

| Component | File | Status |
|---|---|---|
| Contract | `reliability_harness/runtime/execution/contract.py` | Done |
| Local runner | `reliability_harness/runtime/execution/local_runner.py` | Done |
| Execution artifact | `reliability_harness/artifacts/execution_artifact.py` | Done |

**Benchmark-4A.1 boundaries:**
- `execute_locally()` runs trusted fixture code only. It is NOT safe for untrusted agent-generated code.
- Docker-isolated execution for agent-generated code is **Benchmark-4B** (not yet implemented).
- No retry, no memory, no process reliability metrics in this phase.
- No CLI integration in this phase (`run_benchmark.py` and `cli.py` are unchanged).

**Outputs** are written to:
```
outputs/executions/{run_id}/{run_id}_{task_id}.json
```

**Execution artifact schema:**
```json
{
  "artifact_version": "4A.1",
  "created_at": "...",
  "run_id": "...",
  "benchmark": "mbpp",
  "task_id": "mbpp_1",
  "candidate_code": "def add(a, b): return a + b",
  "tests": ["assert add(1, 2) == 3"],
  "source_generation_artifact": null,
  "result": {
    "exit_code": 0,
    "stdout": "",
    "stderr": "",
    "timed_out": false,
    "tests_passed": true,
    "error_type": null,
    "execution_time_ms": 12,
    "docker_used": false,
    "execution_performed": true
  }
}
```

**`error_type` values:** `null` (pass), `assertion_failure`, `syntax_error`, `runtime_error`, `timeout`, `infrastructure_error`, `unknown`.

---

## Benchmark-3: Generation-Only LLM Candidate Generation

Benchmark-3 adds LLM candidate generation on top of the Benchmark-2 data-loading layer.

**Scope:** prompt building → LLM call → code extraction → generation artifact.  
**Not in scope:** code execution, Docker, pass/fail evaluation, retry, reflection, memory, process metrics.

**Entrypoints:**

```bash
# Python module
python -m reliability_harness.experiments.run_benchmark --benchmark tiny --generate --limit 1
python -m reliability_harness.experiments.run_benchmark --benchmark mbpp --generate --limit 2 --model-name deepseek-v4-flash

# CLI
python -m reliability_harness.cli benchmark --benchmark tiny --generate --limit 1
```

**Options:**

| Flag | Default | Description |
|---|---|---|
| `--generate` | off | Enable generation mode (requires DEEPSEEK_API_KEY) |
| `--limit N` | all | Process only the first N tasks |
| `--model-name` | `deepseek-v4-flash` | LLM model identifier |
| `--temperature` | `0.0` | Sampling temperature |
| `--max-tokens` | `1024` | Max tokens per generation |

**Outputs** are written to:

```
outputs/predictions/{run_id}/manifest.json
outputs/predictions/{run_id}/{task_id}.json
```

`run_id` is a timestamp + random suffix, e.g. `20250527_153042_a1b2c3d4`.

**`.env` rules:**
- `--dry-run` never reads `.env` and never requires `DEEPSEEK_API_KEY`.
- `--generate` reads `DEEPSEEK_API_KEY` from `.env` or the environment (via `load_dotenv()` called inside `LLMClient.from_env()` only).
- `.env` is `.gitignore`d — never commit API keys.
- Artifacts record `model_name` only, never the API key.

**Generation artifact schema** (per-task JSON):

```json
{
  "run_id": "...",
  "benchmark": "tiny",
  "task_id": "tiny_0",
  "model_name": "deepseek-v4-flash",
  "prompt": "...",
  "raw_response": "...",
  "extracted_code": "def solve(): ...",
  "extraction_status": "success",
  "error": null,
  "timestamp": "...",
  "llm_used": true,
  "docker_used": false,
  "execution_performed": false
}
```

**Manifest schema:**

```json
{
  "run_id": "...",
  "benchmark": "tiny",
  "model_name": "deepseek-v4-flash",
  "num_tasks": 2,
  "artifacts": ["...path/tiny_0.json", "...path/tiny_1.json"],
  "llm_used": true,
  "docker_used": false,
  "execution_performed": false,
  "timestamp": "..."
}
```

> **Benchmark-3 scope:** LLM candidate generation only. No code execution.
> No Docker. No pass/fail evaluation. No retry/reflection. No memory. No process metrics.

---

## Benchmark-2: MBPP / HumanEval Small Fixture Loading

`mbpp` and `humaneval` now load from local deterministic fixture files.
No LLM, no Docker, no memory, no code execution.

**Fixture files:**
- `data/fixtures/mbpp_small.json` — 2 MBPP-style tasks
- `data/fixtures/humaneval_small.json` — 2 HumanEval-style tasks

```bash
# Shell
bash scripts/run_benchmark_dry_run.sh mbpp
bash scripts/run_benchmark_dry_run.sh humaneval

# Python module
python -m reliability_harness.experiments.run_benchmark --benchmark mbpp --dry-run
python -m reliability_harness.experiments.run_benchmark --benchmark humaneval --dry-run

# CLI
python -m reliability_harness.cli benchmark --benchmark mbpp --dry-run
python -m reliability_harness.cli benchmark --benchmark humaneval --dry-run
```

Each dry-run writes a manifest artifact to:

```
outputs/benchmark_results/mbpp_dry_run.json
outputs/benchmark_results/humaneval_dry_run.json
```

The artifact JSON includes `benchmark`, `adapter`, `status`, `num_tasks`, and path fields.
Both artifact files are covered by `.gitignore` and are not committed to the repo.

> **Benchmark-2 scope:** data loading only. No LLM, no Docker, no memory,
> no code execution, no retry/reflection, no process metrics.

---

## Benchmark-1: Tiny Fixture Dry-Run

`tiny` is a local deterministic fixture benchmark for pipeline smoke tests.
It uses `data/fixtures/tiny_code_tasks.json` (2 tasks). No LLM. No Docker. No memory.

```bash
# Shell
bash scripts/run_benchmark_dry_run.sh tiny

# Python
python -m reliability_harness.experiments.run_benchmark --benchmark tiny --dry-run

# CLI
python -m reliability_harness.cli benchmark --benchmark tiny --dry-run
```

The dry-run writes a manifest to:

```
outputs/benchmark_results/tiny_dry_run.json
```

The JSON includes `benchmark`, `adapter`, `status`, `num_tasks`, and path fields.

---

## Dry-run (Skeleton Validation)

Use `--dry-run` (or `scripts/run_benchmark_dry_run.sh`) to validate the pipeline skeleton.

- `tiny`: loads local fixture file, writes `outputs/benchmark_results/tiny_dry_run.json`.
- `mbpp` / `humaneval`: skeleton only — no data loading, no output writes.

No LLM calls, no Docker, no memory for any benchmark dry-run.

```bash
bash scripts/run_benchmark_dry_run.sh tiny
bash scripts/run_benchmark_dry_run.sh mbpp
bash scripts/run_benchmark_dry_run.sh humaneval

python -m reliability_harness.experiments.run_benchmark --benchmark tiny --dry-run
python -m reliability_harness.experiments.run_benchmark --benchmark mbpp --dry-run
python -m reliability_harness.experiments.run_benchmark --benchmark humaneval --dry-run
```

Also accessible from the unified CLI:

```bash
python -m reliability_harness.cli benchmark --benchmark tiny --dry-run
python -m reliability_harness.cli benchmark --benchmark mbpp --dry-run
python -m reliability_harness.cli benchmark --benchmark humaneval --dry-run
```

---

## Full Run (Coming Next Phase)

Once MBPP/HumanEval data loading is implemented, drop `--dry-run`:

```bash
python -m reliability_harness.experiments.run_benchmark --benchmark mbpp
python -m reliability_harness.experiments.run_benchmark --benchmark humaneval
```

---

## Pipeline (8 Steps)

| Step | Component | Output |
|---|---|---|
| 1 | `benchmarks.registry.get_adapter()` | BenchmarkAdapter instance |
| 2 | `adapter.load_tasks()` + `adapter.normalize()` | list[BenchmarkTask] |
| 3 | `runtime` closed-loop agent | trajectory dict |
| 4 | `sandbox` Docker execution | stdout / stderr / exit code |
| 5 | `runtime.agent.trajectory` | Trajectory object |
| 6 | `evaluation.runtime_eval` | eval_result dict |
| 7 | `artifacts.run_artifact.save_run_artifact()` | `outputs/runs/run_*.json` |
| 8 | `reporting.reliability_report.generate_report()` | `outputs/reports/reliability_report.*` |

---

## Path Policy

| Purpose | Path |
|---|---|
| Task fixtures | `data/tasks/` |
| Experiment fixtures | `data/fixtures/` |
| Run artifacts | `outputs/runs/` |
| Reliability reports | `outputs/reports/` |
| Benchmark summaries | `outputs/benchmark_results/` |

All paths are resolved from repo root via `reliability_harness.utils.paths` — independent of `cwd`.

---

## Memory Isolation Policy

Official benchmark runs **do not** reuse legacy ReActX memory by default.

- The default Chroma collection is `reliability_failure_memory` (not `reactx_failure_memory`).
- Persistent memory is **disabled** in dry-run and skeleton phases.
- To enable persistent memory in a full run, set:
  ```bash
  export RELIABILITY_HARNESS_MEMORY_COLLECTION=reliability_failure_memory
  ```
- `REACTX_MEMORY_COLLECTION` is a deprecated explicit alias; it is only read when explicitly set by the user and will emit a `DeprecationWarning`.
- Legacy `data/chroma_db_data/` collections from the ReActX prototype phase are **excluded** from paper results. Do not enable them for official benchmark runs.

---

## What NOT to Use for Paper Results

| Script / Entry | Status | Reason |
|---|---|---|
| `legacy/ReActX/benchmark_reliability.py` | **Archived / Deprecated** | EvalForge-era; not connected to ReliabilityHarness pipeline |
| `legacy/ReActX/evaluate.py` | **Archived / Deprecated** | Legacy EvalForge runner |
| `run_eval.py` | **Legacy** | EvalForge-style; outputs not canonical for paper |
| `scripts/legacy/run_benchmark_mock.sh` | **Legacy** | Calls run_eval.py (EvalForge-era); use `scripts/run_benchmark_dry_run.sh` instead |
| `legacy/ReActX/test_*.py` | **Archived / Legacy smoke tests** | Not constraints on new architecture; root `tests/` supersedes these |
| `legacy/ReActX/benchmark_results/` | **Historical data** | Not paper results; not to be cited |
| `legacy/ReActX/runs/` | **Historical data** | Not paper results |
| `legacy/ReActX/reports/` | **Historical data** | Not paper results |

## Root-level Tests (Migration-4A/B + 4C, Authoritative)

Official benchmark skeleton tests live in `tests/` (repo root). These are the
authoritative constraints on the Benchmark-0 skeleton.

```bash
# Official test entrypoint (Migration-4C)
bash scripts/run_tests.sh

# Or run specific files directly
python -m pytest tests/test_benchmark_entrypoint.py
python -m pytest tests/test_benchmark_registry.py
python -m pytest tests/test_benchmark_task_schema.py
```

These tests:
- Only import `reliability_harness.*`.
- Do not call LLMs, Docker, or load real benchmark data.
- Supersede `legacy/ReActX/test_*.py` as new-architecture constraints.

`legacy/ReActX/test_*.py` tests are archived legacy migration checks only. They are NOT
acceptance criteria for the paper benchmark path. Manual legacy runs are
available via `scripts/legacy/run_reactx_tests.sh`.

---

## Official Benchmark Artifacts

Current ReliabilityHarness benchmark artifacts are generated by:

```bash
python -m reliability_harness.experiments.run_benchmark --benchmark <name>
```

And written to:

| Output | Path |
|--------|------|
| Run artifacts | `outputs/runs/run_*.json` |
| Reliability reports | `outputs/reports/` |
| Benchmark summaries | `outputs/benchmark_results/` |

**Note:** `docs/legacy/examples/` contains historical snapshots from the ReActX prototype phase only. They use a pre-migration schema and are **not** paper results. Do not cite them as current ReliabilityHarness outputs.

---

## Adding a New Benchmark

1. Create `reliability_harness/benchmarks/adapters/<name>.py` subclassing `BenchmarkAdapter`.
2. Implement `load_tasks()` and `normalize()`.
3. Register in `reliability_harness/benchmarks/registry.py` `_REGISTRY`.
4. Add task fixtures to `data/tasks/<name>/`.
5. Test with `--dry-run`, then without.
