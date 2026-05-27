# ReliabilityHarness — Migration Plan

## Migration-1: ReActX/EvalForge → reliability_harness (current)

**Branch:** `migration/reliability-harness-structure`

### What Migration-1 completes

1. Creates `reliability_harness/` as the primary Python package.
2. Moves all core code from `ReActX/app/` → `reliability_harness/runtime/`, `reliability_harness/core/`, `reliability_harness/evaluation/runtime_eval/`, `reliability_harness/artifacts/`, `reliability_harness/reporting/`, `reliability_harness/reasoning/`, `reliability_harness/memory/`, `reliability_harness/sandbox/client.py`.
3. Moves `ReActX/evalforge/` → `reliability_harness/evaluation/` (metrics, runner, tasks, model_registry, analysis, datasets, reports, scheduler, models).
4. Moves `ReActX/sandbox/executor.py` and `sandbox/main.py` → `reliability_harness/sandbox/`.
5. Creates compatibility shims `app/` and `evalforge/` at repo root to keep existing `ReActX/test_*.py` tests runnable.
6. Creates `reliability_harness/utils/paths.py` with full path constant set.
7. Creates `reliability_harness/cli.py` (`info` and `paths` subcommands).
8. Creates `docker/backend.Dockerfile`, `docker/sandbox.Dockerfile`, `docker/docker-compose.yml` targeting `reliability_harness.*`.
9. Updates `run_eval.py` imports to `reliability_harness.evaluation.*`.
10. Updates `configs/benchmark_eval.yaml` and `configs/leaderboard_eval.yaml`: `project.name: ReliabilityHarness`.
11. Creates `scripts/run_paths.sh`, `scripts/run_tests.sh`, `scripts/run_benchmark_mock.sh`.
12. Updates README.md to use `reliability_harness` as primary package.
13. Creates `docs/ARCHITECTURE.md` and `docs/MIGRATION_PLAN.md`.

### Remaining legacy references after Migration-1

- `ReActX/app/` and `ReActX/evalforge/` directories remain on disk (not deleted). They are no longer the primary code source.
- `ReActX/test_*.py` still import from `app.*` / `utils.*` and run with `ReActX/` in PYTHONPATH.
- `chroma_db_data` is still referenced under `ReActX/chroma_db_data` in Docker compose (annotated for follow-up).
- `ReActX/utils/dataset_loader.py` is still the source for `utils.dataset_loader` imports inside `ReActX/test_*.py`.
- `reliability_harness/sandbox/main.py` title still says "ReActX Sandbox Service" (cosmetic; not changed to avoid business logic drift).

### What was NOT changed in Migration-1

- No evaluation semantics (success, recovery, score logic).
- No agent decision logic.
- No retry / reflection / memory retrieval behavior.
- No metric implementation logic.
- No sandbox execution semantics.
- No new benchmarks (MBPP, HumanEval, LiveCodeBench, SWE-bench).
- No OCR / DocAI legacy cleanup.
- No deletion of historical benchmark result JSON.
- No git add / commit / push.

---

## Migration-2A: Docker and runtime path stabilization (completed)

**Branch:** `migration/reliability-harness-structure`

### What Migration-2A completes

1. Creates root-level `requirements.txt` from `ReActX/requirements.txt` (deduped, invalid entry removed).
2. Creates `docker/sandbox.requirements.txt` from `ReActX/sandbox/requirements.txt`; sandbox Dockerfile no longer references `ReActX/` path.
3. Fixes `docker/docker-compose.yml` chroma volume: `/app/ReActX/chroma_db_data` → `/app/data/chroma_db_data`.
4. Adds `DATA_ROOT`, `RUNS_ROOT`, `CHROMA_DB_ROOT`, `OUTPUTS_ROOT` and helper functions to `reliability_harness/utils/paths.py`.
5. Fixes `reliability_harness/core/rag.py`: replaces cwd-relative `./chroma_db_data` with `CHROMA_DB_ROOT` from paths module.
6. Creates `.env.example` documenting required env vars; `docker-compose.yml` reads `../.env` (repo root).
7. Sets `env_file.required: false` in `docker-compose.yml` so `docker compose config` passes without a local `.env` file. Real experiment runs still require the user to create repo root `.env` from `.env.example`.

### What Migration-2A does NOT change

- No evaluation semantics, agent logic, retry/reflection/memory behavior.
- `reliability_harness/utils/dataset_loader.py` legacy paths unchanged (Migration-2B).
- `reliability_harness/memory/store.py` unchanged (Migration-2B).
- `ReActX/app/` and `ReActX/evalforge/` not deleted (Migration-3).
- `ReActX/test_*.py` not migrated (Migration-3).
- No MBPP/HumanEval/SWE-bench changes.

---

## Migration-2B-1: Unify data root and generated output paths (completed)

**Branch:** `migration/reliability-harness-structure`

### What Migration-2B-1 completes

1. Establishes canonical constants in `reliability_harness/utils/paths.py`:
   - Input: `DATA_ROOT`, `TASKS_ROOT`, `CHROMA_DB_ROOT`, `FAILURE_MEMORY_PATH`
   - Output: `OUTPUTS_ROOT`, `RUNS_ROOT`, `REPORTS_ROOT`, `PREDICTIONS_ROOT`, `BENCHMARK_RESULTS_ROOT`
   - Helper functions: `tasks_path()`, `failure_memory_path()`, `runs_path()`, `reports_path()`, `predictions_path()`, `benchmark_results_path()`
2. Updates `dataset_loader.py`: new env var priority (`RELIABILITY_HARNESS_DATASET_PATH` > `DATASET_PATH` > `REACTX_DATASET_PATH`); canonical `data/` paths checked first; `ReActX/` paths kept as legacy fallback until Migration-3.
3. Updates `memory/store.py`: default failure memory path is now `FAILURE_MEMORY_PATH` (`data/failure_memory.jsonl`), not cwd-relative.
4. Updates `artifacts/run_artifact.py`: default run artifact output is now `RUNS_ROOT` (`outputs/runs/`).
5. Updates `reporting/reliability_report.py`: default I/O is now `RUNS_ROOT` / `REPORTS_ROOT` (`outputs/runs/`, `outputs/reports/`).
6. Fixes `docker/docker-compose.yml` Chroma volume: `../chroma_db` → `../data/chroma_db_data` (host path now matches container path).
7. Updates `configs/benchmark_eval.yaml`: `prediction_output_root: eval_data/runs` → `outputs/predictions`.
8. Creates `data/`, `data/tasks/`, `outputs/`, `outputs/runs/`, `outputs/reports/`, `outputs/predictions/`, `outputs/benchmark_results/` directory scaffolding via `.gitkeep`.
9. Updates `.gitignore`: generated output contents ignored, `.gitkeep` files and task fixtures preserved; `!.env.example` added.
10. Updates `.env.example`: documents new `RELIABILITY_HARNESS_DATASET_PATH` and `DATASET_PATH` overrides.

### What Migration-2B-1 does NOT change

- No evaluation semantics, agent logic, retry/reflection/memory retrieval behavior.
- No business logic in `closed_loop_runner.py`, `evaluator.py`, or metric modules.
- `ReActX/data/` is **not moved** — legacy data files remain in place; `dataset_loader.py` keeps `ReActX/` as final fallback.
- Historical benchmark result JSON in `ReActX/benchmark_results/` is not moved.
- `ReActX/app/` and `ReActX/evalforge/` not deleted.
- `ReActX/test_*.py` not migrated.
- No MBPP/HumanEval/SWE-bench changes.
- `reactx_failure_memory` collection name not renamed (Migration-3).
- `ReActXAgent` class name not renamed (Migration-3).

---

## Benchmark-0: Benchmark adapter skeleton and experiment entrypoint (completed)

**Branch:** `migration/reliability-harness-structure`

### What Benchmark-0 completes

1. Creates `reliability_harness/benchmarks/task_schema.py`: `BenchmarkTask` dataclass — canonical schema between adapter layer and runtime/evaluation layers.
2. Creates `reliability_harness/benchmarks/adapters/base.py`: `BenchmarkAdapter` ABC with abstract `load_tasks()` and `normalize()` methods.
3. Creates `reliability_harness/benchmarks/adapters/mbpp.py`: `MBPPAdapter` stub with documented field mapping; raises `NotImplementedError` until data loading is implemented.
4. Creates `reliability_harness/benchmarks/adapters/humaneval.py`: `HumanEvalAdapter` stub with documented field mapping; raises `NotImplementedError` until data loading is implemented.
5. Creates `reliability_harness/benchmarks/registry.py`: `get_adapter()` and `list_benchmarks()` dispatch; `_REGISTRY` maps benchmark name → adapter class.
6. Creates `reliability_harness/experiments/run_benchmark.py`: sole authoritative entrypoint for paper benchmark runs; supports `--benchmark` and `--dry-run`; `dry_run()` returns structured pipeline manifest without loading data; `run()` raises `NotImplementedError` for full execution until adapters are complete.
7. Updates `reliability_harness/cli.py`: adds `benchmark` subcommand (`--benchmark`, `--dry-run`) that delegates to `run_benchmark.run()`.
8. Adds legacy comment header to `run_eval.py` marking it as EvalForge-era; not for paper results.
9. Adds legacy comment header to `scripts/run_benchmark_mock.sh` marking it as transitional.
10. Creates `docs/BENCHMARK_ENTRYPOINT.md`: full reference for paper benchmark entrypoint, pipeline steps, path policy, deprecated scripts, and adapter extension guide.
11. Updates `README.md`: adds "Benchmark Entrypoint" section documenting authoritative entrypoint, dry-run and full-run usage, deprecated entry points table.
12. Updates `docs/ARCHITECTURE.md`: adds Layer 8 (Benchmarks layer) documenting `reliability_harness.benchmarks` and `reliability_harness.experiments`.

### New data and output paths

| Purpose | Path |
|---|---|
| Task fixtures | `data/tasks/` |
| Experiment fixtures | `data/fixtures/` |
| Run artifacts | `outputs/runs/` |
| Reliability reports | `outputs/reports/` |
| Benchmark summaries | `outputs/benchmark_results/` |

All paths resolved via `reliability_harness.utils.paths` — no `os.getcwd()` dependency.

### What Benchmark-0 does NOT change

- No evaluation semantics, agent logic, retry/reflection/memory behavior.
- No business logic in any existing module.
- `MBPPAdapter.load_tasks()` and `HumanEvalAdapter.load_tasks()` both raise `NotImplementedError` — no data loading implemented.
- Full execution (`run()` without `--dry-run`) raises `NotImplementedError` — not yet implemented.
- `ReActX/benchmark_results/`, `ReActX/runs/`, `ReActX/reports/` not moved (historical data, not paper results).
- `ReActX/app/`, `ReActX/evalforge/`, `app/`, `evalforge/` not deleted.
- `ReActX/test_*.py` not migrated.
- No SWE-bench support (roadmap: MBPP → HumanEval → LiveCodeBench → SWE-bench Lite).

---

## Migration-4A/B: Official entrypoint cleanup and root benchmark tests (completed)

**Branch:** `migration/reliability-harness-structure`

### What Migration-4A/B completes

1. Creates `scripts/run_benchmark_dry_run.sh`: official shell entrypoint for dry-run benchmark validation. Works from any cwd. No ReActX / run_eval.py / EvalForge dependencies. No LLM calls, no data loading, no output writes.
2. Creates `tests/test_benchmark_entrypoint.py`: root-level tests for `reliability_harness.experiments.run_benchmark`. Tests dry-run manifest for mbpp and humaneval. Tests that full run (non-dry-run) raises `NotImplementedError`.
3. Creates `tests/test_benchmark_registry.py`: root-level tests for `reliability_harness.benchmarks.registry`. Tests `get_adapter("mbpp")` returns `MBPPAdapter`, `get_adapter("humaneval")` returns `HumanEvalAdapter`, unknown benchmark raises `ValueError`.
4. Creates `tests/test_benchmark_task_schema.py`: root-level tests for `reliability_harness.benchmarks.task_schema.BenchmarkTask`. Tests all fields, defaults, `to_dict()` / `from_dict()` roundtrip.
5. Updates `README.md` Quick Start: `scripts/run_benchmark_dry_run.sh` and `python -m reliability_harness.experiments.run_benchmark --dry-run` are the primary recommended commands. Deprecated table updated.
6. Updates `docs/BENCHMARK_ENTRYPOINT.md`: adds Migration-4A/B status note; documents `scripts/run_benchmark_dry_run.sh` as official shell entrypoint; updates deprecated table; documents root-level tests.
7. Updates `docs/ARCHITECTURE.md`: adds "Current Migration Status" table; documents Migration-4A/B completion.
8. Updates `scripts/run_benchmark_mock.sh`: adds explicit LEGACY header; references new entrypoint. Behavior unchanged.
9. Updates `scripts/run_tests.sh`: adds note about new root tests and legacy status of `ReActX/test_*.py`. Behavior unchanged.

### What Migration-4A/B does NOT change

- No evaluation semantics, agent logic, retry/reflection/memory behavior.
- No business logic in any existing module.
- `ReActX/` directory not deleted; `ReActX/test_*.py` not deleted or moved.
- `app/` and `evalforge/` shims not deleted.
- No MBPP/HumanEval data loading implemented.
- No SWE-bench or LiveCodeBench work.
- No git add / commit / push.

---

## Migration-4C: Split official tests from legacy ReActX tests (completed)

**Branch:** `migration/reliability-harness-structure`

### What Migration-4C completes

1. Rewrites `scripts/run_tests.sh`: now runs only root-level `tests/` via pytest. No `PYTHONPATH=ReActX`. No call to `ReActX/run_tests.py`. Official ReliabilityHarness test entrypoint.
2. Creates `scripts/legacy/run_reactx_tests.sh`: isolated legacy runner for old ReActX tests. Prints a visible WARNING banner clarifying legacy status. Contains the `PYTHONPATH=ReActX` and `cd ReActX && python run_tests.py` logic moved out of the official script.
3. Updates `README.md`: Quick Start test command is `bash scripts/run_tests.sh`. Legacy table updated to reference `scripts/legacy/run_reactx_tests.sh`.
4. Updates `docs/BENCHMARK_ENTRYPOINT.md`: documents `bash scripts/run_tests.sh` as official test entrypoint; documents `scripts/legacy/run_reactx_tests.sh` as legacy-only.
5. Updates `docs/ARCHITECTURE.md`: adds "Test Layer" section clearly separating authoritative `tests/` from legacy `ReActX/test_*.py`; updates migration status table.

### What Migration-4C does NOT change

- No evaluation semantics, agent logic, retry/reflection/memory behavior.
- No business logic in any module.
- `ReActX/` directory, `ReActX/test_*.py`, `ReActX/run_tests.py` — not deleted, not moved.
- `app/` and `evalforge/` shims — not deleted.
- No MBPP/HumanEval data loading.
- No git add / commit / push.

---

## Migration-2B-2: Physical data migration (next)

Planned scope:
- Copy `ReActX/data/tasks/reactx_closed_loop_tasks.json` → `data/tasks/reliability_tasks.json`.
- Copy `ReActX/data/reliability_tasks.json` if present → `data/`.
- Move host `chroma_db_data/` content → `data/chroma_db_data/` (after service stop).
- Move `ReActX/benchmark_results/` → `outputs/benchmark_results/` (historical data).
- After copy verified: remove legacy fallback paths from `dataset_loader.py`.
- Update `REACTX_DATASET_PATH` references to use new name.

Each phase must be committed separately.

---

## Migration-3: Test migration and legacy cleanup (future)

Planned scope:
- Move `ReActX/test_*.py` → `tests/` (repo root).
- Update test imports to `reliability_harness.*`.
- Remove `app/` and `evalforge/` shims when no longer needed.
- Remove `ReActX/app/` and `ReActX/evalforge/` duplicate legacy directories.
- Rename cosmetic legacy identifiers (`ReActXAgent`, `run_evalforge`, `reactx_failure_memory`) as a batch.

---

## Migration-4: MBPP/HumanEval benchmark adapter (future)

Planned scope (after Migration-1–3 stabilize):
- Implement dataset adapter for MBPP and HumanEval.
- Wire into `reliability_harness.evaluation.runner`.
- Do NOT start SWE-bench until MBPP/HumanEval basics work.
