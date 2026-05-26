# ReliabilityHarness — Benchmark Entrypoint Reference

## Formal Paper Experiment Entrypoint

The sole authoritative entrypoint for ReliabilityHarness paper experiments is:

```bash
python -m reliability_harness.experiments.run_benchmark --benchmark <name> [--dry-run]
```

Supported benchmarks: `mbpp`, `humaneval`

---

## Dry-run (Skeleton Validation)

Use `--dry-run` to validate the pipeline skeleton without loading data, calling
LLMs, or writing outputs. Safe to run at any time.

```bash
python -m reliability_harness.experiments.run_benchmark --benchmark mbpp --dry-run
python -m reliability_harness.experiments.run_benchmark --benchmark humaneval --dry-run
```

Also accessible from the CLI:

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
| `ReActX/benchmark_reliability.py` | **Deprecated** | EvalForge-era; not connected to ReliabilityHarness evaluation pipeline |
| `ReActX/evaluate.py` | **Deprecated** | Legacy EvalForge runner |
| `run_eval.py` | **Legacy** | EvalForge-style; outputs not canonical for paper |
| `scripts/run_benchmark_mock.sh` | **Transitional** | Calls run_eval.py; use run_benchmark --dry-run instead |
| `ReActX/test_*.py` | **Legacy smoke tests** | Not constraints on new architecture; will migrate to tests/ in Migration-3 |
| `ReActX/benchmark_results/` | **Historical data** | Not paper results; not to be cited |
| `ReActX/runs/` | **Historical data** | Not paper results |
| `ReActX/reports/` | **Historical data** | Not paper results |

---

## Adding a New Benchmark

1. Create `reliability_harness/benchmarks/adapters/<name>.py` subclassing `BenchmarkAdapter`.
2. Implement `load_tasks()` and `normalize()`.
3. Register in `reliability_harness/benchmarks/registry.py` `_REGISTRY`.
4. Add task fixtures to `data/tasks/<name>/`.
5. Test with `--dry-run`, then without.
