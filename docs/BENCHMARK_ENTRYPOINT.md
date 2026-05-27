# ReliabilityHarness — Benchmark Entrypoint Reference

> **Migration-4A/B status:** Benchmark-0 skeleton is complete.
> Root-level `tests/` are the authoritative test constraints for the new architecture.
> `ReActX/test_*.py` are legacy and are NOT constraints on `reliability_harness.*`.

## Formal Paper Experiment Entrypoints

The sole authoritative entrypoints for ReliabilityHarness paper experiments are:

**Shell (recommended):**
```bash
bash scripts/run_benchmark_dry_run.sh mbpp
bash scripts/run_benchmark_dry_run.sh humaneval
```

**Python module:**
```bash
python -m reliability_harness.experiments.run_benchmark --benchmark <name> [--dry-run]
```

Supported benchmarks: `mbpp`, `humaneval`

> **Current phase:** dry-run only. Full benchmark execution (data loading, agent runtime,
> sandbox) is not yet implemented. Full run will be enabled in the next benchmark phase.

---

## Dry-run (Skeleton Validation)

Use `--dry-run` (or `scripts/run_benchmark_dry_run.sh`) to validate the pipeline
skeleton without loading data, calling LLMs, or writing outputs. Safe to run at any time.

```bash
bash scripts/run_benchmark_dry_run.sh mbpp
bash scripts/run_benchmark_dry_run.sh humaneval

python -m reliability_harness.experiments.run_benchmark --benchmark mbpp --dry-run
python -m reliability_harness.experiments.run_benchmark --benchmark humaneval --dry-run
```

Also accessible from the unified CLI:

```bash
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

## What NOT to Use for Paper Results

| Script / Entry | Status | Reason |
|---|---|---|
| `ReActX/benchmark_reliability.py` | **Deprecated** | EvalForge-era; not connected to ReliabilityHarness pipeline |
| `ReActX/evaluate.py` | **Deprecated** | Legacy EvalForge runner |
| `run_eval.py` | **Legacy** | EvalForge-style; outputs not canonical for paper |
| `scripts/legacy/run_benchmark_mock.sh` | **Legacy** | Calls run_eval.py (EvalForge-era); use `scripts/run_benchmark_dry_run.sh` instead |
| `ReActX/test_*.py` | **Legacy smoke tests** | Not constraints on new architecture; root `tests/` supersedes these |
| `ReActX/benchmark_results/` | **Historical data** | Not paper results; not to be cited |
| `ReActX/runs/` | **Historical data** | Not paper results |
| `ReActX/reports/` | **Historical data** | Not paper results |

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
- Supersede `ReActX/test_*.py` as new-architecture constraints.

`ReActX/test_*.py` tests are legacy migration checks only. They are NOT
acceptance criteria for the paper benchmark path. Manual legacy runs are
available via `scripts/legacy/run_reactx_tests.sh`.

---

## Adding a New Benchmark

1. Create `reliability_harness/benchmarks/adapters/<name>.py` subclassing `BenchmarkAdapter`.
2. Implement `load_tasks()` and `normalize()`.
3. Register in `reliability_harness/benchmarks/registry.py` `_REGISTRY`.
4. Add task fixtures to `data/tasks/<name>/`.
5. Test with `--dry-run`, then without.
