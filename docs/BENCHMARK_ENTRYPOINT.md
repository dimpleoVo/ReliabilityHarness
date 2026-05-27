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
python -m reliability_harness.experiments.run_benchmark --benchmark mbpp --generate --limit 2 --model-name deepseek-chat

# CLI
python -m reliability_harness.cli benchmark --benchmark tiny --generate --limit 1
```

**Options:**

| Flag | Default | Description |
|---|---|---|
| `--generate` | off | Enable generation mode (requires DEEPSEEK_API_KEY) |
| `--limit N` | all | Process only the first N tasks |
| `--model-name` | `deepseek-chat` | LLM model identifier |
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
  "model_name": "deepseek-chat",
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
  "model_name": "deepseek-chat",
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
