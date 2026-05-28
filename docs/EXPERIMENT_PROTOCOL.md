# ReliabilityHarness — Manual Experiment Protocol

> See also: [BENCHMARK_ENTRYPOINT.md](BENCHMARK_ENTRYPOINT.md) for entrypoint reference and artifact schemas.

---

## A. Purpose

This protocol records the manual experiment procedures used for:

1. **Controlled pipeline validation** — verifying the generate → execute → summarize → aggregate artifact chain end-to-end under known inputs and expected outputs.
2. **Small smoke experiments** — running a minimal number of tasks and runs to confirm that pipeline components produce machine-readable artifacts suitable for paper evidence.

**This is not a full benchmark protocol.**  
It does not cover batch execution, LLM-as-judge evaluation, retry/recovery analysis, reasoning consistency, tool correctness, or memory-assisted recovery. All rates and distributions produced by controlled tiny experiments are pipeline validation results, not model performance measurements.

---

## B. Current Artifact Pipeline

Each experiment run produces four artifact types in sequence:

| Artifact | Path pattern | Produced by |
|---|---|---|
| **Generation artifact** | `outputs/predictions/{run_id}/{task_id}.json` | `--generate` mode |
| **Execution artifact** | `outputs/executions/{run_id}/{run_id}_{task_id}.json` | `--execute-generation-artifact` mode |
| **Run summary artifact** | `outputs/artifacts/run_summaries/{run_id}_{task_id}_summary.json` | auto-written after execution |
| **Aggregate summary artifact** | `outputs/artifacts/aggregate_summaries/aggregate_summary_{timestamp}.json` | `--aggregate-run-summaries` mode |

The pipeline is strictly sequential per task. Aggregate summaries are computed from explicit per-task run summary paths; they do not execute code, call LLMs, or use Docker.

All `outputs/*` paths are covered by `.gitignore` and are never committed.

---

## C. Controlled Tiny Success-Path Protocol (Benchmark-7A)

**Name:** Benchmark-7A tiny controlled multi-run  
**Status:** Completed and audited.

**Parameters:**

| Parameter | Value |
|---|---|
| Benchmark | `tiny` |
| Model | `deepseek-v4-flash` |
| Tasks | `tiny_001`, `tiny_002` |
| Independent generation runs | 3 |
| Execution runner | Docker |
| Expected total run summaries | 6 (3 runs × 2 tasks) |
| Expected aggregate `total_runs` | 6 |

**Procedure:**

1. Run `--generate` three independent times with `--benchmark tiny --limit 2`. Each run produces a distinct `run_id` and two per-task generation artifacts.
2. For each generation artifact, run `--execute-generation-artifact` with Docker. Each execution auto-writes a run summary artifact.
3. Collect all 6 run summary artifact paths (explicit, not glob).
4. Run `--aggregate-run-summaries` with the 6 explicit paths to produce one aggregate summary artifact.
5. Verify `aggregate_summary.counts.total_runs == 6`.
6. Record the aggregate summary artifact path for paper log.

**Expected success-path aggregate fields:**

```json
{
  "counts": { "total_runs": 6, "final_success_count": 6 },
  "rates": { "final_success_rate": 1.0, "failure_observed_rate": 0.0 },
  "distributions": { "failure_type_distribution": { "none": 6 } }
}
```

---

## D. Controlled Failure-Path Protocol (Benchmark-7A-F)

**Name:** Benchmark-7A-F controlled assertion failure validation  
**Status:** Completed and audited.

**Parameters:**

| Parameter | Value |
|---|---|
| Benchmark | `tiny` fixture (controlled) |
| `llm_used` | `false` (manually crafted fixture, no LLM call) |
| Task | `tiny_001` |
| Injected code | `return a - b` (intentionally wrong implementation) |
| Expected failure type | `assertion_failure` |
| Aggregate input | 6 success summaries (from 7A) + 1 controlled failure summary |
| Expected aggregate `total_runs` | 7 |

**Procedure:**

1. Construct a generation artifact manually with `extraction_status: "success"`, `llm_used: false`, and `extracted_code: "return a - b"` for `tiny_001`.
2. Run `--execute-generation-artifact` on the controlled artifact with Docker. The test assertions will fail, producing `tests_passed: false`, `error_type: "assertion_failure"`.
3. The auto-written run summary will have `diagnostics.failure.failure_type == "assertion_failure"` and `success.final_success == false`.
4. Aggregate the 6 Benchmark-7A success summaries plus this 1 controlled failure summary (7 explicit paths total).
5. Verify `aggregate_summary.counts.total_runs == 7` and `distributions.failure_type_distribution` includes `assertion_failure: 1`.

**Expected failure-path aggregate fields:**

```json
{
  "counts": { "total_runs": 7, "final_success_count": 6 },
  "rates": { "final_success_rate": 0.857..., "failure_observed_rate": 0.142..." },
  "distributions": {
    "failure_type_distribution": { "none": 6, "assertion_failure": 1 }
  }
}
```

---

## E. Artifact Selection Rules

These rules apply to any aggregate summary used as paper evidence.

1. **Use explicit run summary paths only.**  
   The `--aggregate-run-summaries` command must receive explicit shell-expanded paths, not Python-internal globs or directory paths.

2. **Do not use broad glob patterns for paper evidence.**  
   `outputs/artifacts/run_summaries/*.json` will include all run summaries in the directory, potentially mixing results from different experiments, models, dates, and controlled fixtures. This produces an undefined and unreproducible aggregate.

3. **Do not mix historical test summaries with experiment summaries.**  
   Any run summary produced during unit testing or CI (even if written to `outputs/`) must not be included in paper-evidence aggregates.

4. **Record every aggregate input path explicitly in the paper log.**  
   The aggregate artifact's `input.run_summary_paths` field records which summaries were included. Verify this field after aggregation.

5. **Controlled fixture summaries and real LLM summaries must not be mixed** unless the experiment design explicitly calls for it and the mixture is documented.

---

## F. Command Templates

All commands use the `reliability_harness.cli` entrypoint. The `run_benchmark` module entrypoint is equivalent.

**Generate tiny (one run, 2 tasks, real LLM):**
```bash
python -m reliability_harness.cli benchmark \
  --benchmark tiny \
  --generate \
  --limit 2 \
  --model-name deepseek-v4-flash
# Requires DEEPSEEK_API_KEY in .env
# Produces: outputs/predictions/{run_id}/tiny_001.json
#           outputs/predictions/{run_id}/tiny_002.json
```

**Execute a generation artifact with Docker:**
```bash
python -m reliability_harness.cli benchmark \
  --execute-generation-artifact outputs/predictions/<run_id>/tiny_001.json \
  --execution-timeout-ms 10000
# Produces: outputs/executions/<run_id>/<run_id>_tiny_001.json  (execution artifact)
#           outputs/artifacts/run_summaries/<run_id>_tiny_001_summary.json  (run summary)
```

**Aggregate explicit run summaries:**
```bash
python -m reliability_harness.cli benchmark \
  --aggregate-run-summaries \
    outputs/artifacts/run_summaries/<run_id_1>_tiny_001_summary.json \
    outputs/artifacts/run_summaries/<run_id_1>_tiny_002_summary.json \
    outputs/artifacts/run_summaries/<run_id_2>_tiny_001_summary.json \
    outputs/artifacts/run_summaries/<run_id_2>_tiny_002_summary.json \
    outputs/artifacts/run_summaries/<run_id_3>_tiny_001_summary.json \
    outputs/artifacts/run_summaries/<run_id_3>_tiny_002_summary.json
# Produces: outputs/artifacts/aggregate_summaries/aggregate_summary_{timestamp}.json
# No LLM, no Docker, no API key required.
```

**Verify working tree is clean before and after an experiment:**
```bash
git status --short
# Expected output: (empty — no staged or unstaged changes)
```

---

## G. Paper Log Checklist

Record the following for every experiment used as paper evidence:

- [ ] **Date** — ISO 8601 (e.g. `2026-05-28`)
- [ ] **Branch** — `git branch --show-current`
- [ ] **Commit** — `git rev-parse --short HEAD`
- [ ] **Model** — model name as recorded in generation artifacts (e.g. `deepseek-v4-flash`)
- [ ] **Benchmark** — benchmark name (e.g. `tiny`)
- [ ] **Task IDs** — list of task IDs included (e.g. `tiny_001`, `tiny_002`)
- [ ] **Run IDs** — all `run_id` values for generation runs included
- [ ] **Generation artifact paths** — one per (run\_id, task\_id) pair
- [ ] **Execution artifact paths** — one per (run\_id, task\_id) pair
- [ ] **Run summary artifact paths** — one per (run\_id, task\_id) pair
- [ ] **Aggregate summary artifact path** — the final `aggregate_summary_{timestamp}.json`
- [ ] **`counts.total_runs`** — from aggregate summary
- [ ] **`rates.final_success_rate`** — from aggregate summary
- [ ] **`rates.observable_process_success_rate`** — from aggregate summary
- [ ] **`rates.failure_observed_rate`** — from aggregate summary
- [ ] **`distributions.failure_type_distribution`** — from aggregate summary
- [ ] **`distributions.failure_stage_distribution`** — from aggregate summary
- [ ] **Limitations** — see Section H; always record which metrics are NOT present

---

## H. Interpretation Rules

These rules apply to all metrics produced by this pipeline. Violation of these rules constitutes misrepresentation of results.

**`final_success_rate`**  
Fraction of runs where `extraction_status == "success"` AND `execution_performed == true` AND `tests_passed == true`.  
This is a **final execution success proxy only**. It does not reflect retry behavior, trajectory quality, reasoning consistency, tool correctness, or memory-assisted recovery. It is not a full reliability score.

**`observable_process_success_rate`**  
Fraction of runs where all minimal observable pipeline stages succeeded (generation, extraction, execution).  
This is derived from minimal observable artifact fields (Benchmark-5A). It is **not** full process correctness. `is_full_process_reliability_metric` is always `false`.

**`diagnostics.failure`**  
Provides minimal observable failure type and stage signals derived from artifact fields.  
This is **not full root-cause taxonomy**. It does not include LLM-as-judge analysis, reasoning trace, tool correctness, or retry classification. `is_full_failure_taxonomy` is always `false`.

**Tiny controlled validation experiments**  
Results from `benchmark: tiny` with 2–6 tasks are pipeline validation results only.  
They are **not model performance evaluations**. Do not extrapolate from `tiny` results to production benchmark performance.

---

## I. 7B Small Smoke — Next Step (Placeholder)

The next experimental phase (Benchmark-7B) will extend this protocol to small MBPP and HumanEval smoke runs.

**Anticipated parameters:**

| Parameter | Anticipated value |
|---|---|
| Benchmarks | `mbpp`, `humaneval` |
| Tasks per benchmark | small subset (e.g. 2–5 tasks) |
| Runs | 1–3 independent generation runs |
| Execution | Docker |
| Aggregate | per-benchmark aggregate summary |

**7B is still not a full benchmark.**  
A small MBPP/HumanEval smoke run validates that the adapter, generation, execution, and aggregation pipeline works end-to-end on non-tiny fixture data. It is not a representative sample for model performance claims.

Full MBPP/HumanEval benchmark experiments (covering statistically meaningful task counts) are a future phase beyond 7B.

This placeholder section will be replaced with a completed protocol entry once 7B is executed and audited.
