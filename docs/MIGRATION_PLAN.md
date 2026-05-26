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

## Migration-2B: Data directory migration (next)

Planned scope:
- Move `ReActX/data/` → `data/` (repo root).
- Move `ReActX/benchmark_results/` → `benchmark_results/` (repo root).
- Move host `chroma_db/` → `data/chroma_db_data/` to match container path.
- Update `reliability_harness/utils/dataset_loader.py`: replace `_LEGACY_REACTX_DATA_ROOT` with `DATA_ROOT` from paths.
- Update `reliability_harness/memory/store.py` if it holds legacy paths.
- Update `REACTX_DATASET_PATH` env var docs.

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
