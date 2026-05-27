# legacy/ — Archived Historical Materials

This directory contains historical and deprecated implementation materials from the ReActX / EvalForge prototype phase.

**These are NOT official ReliabilityHarness experiment entrypoints.**
**Do not use these directories for paper results.**

---

## Contents

| Path | Description |
|------|-------------|
| `legacy/ReActX/` | Archived historical implementation directory. Contains the original ReActX prototype code, legacy tests, historical benchmark results, runs, and reports. |
| `legacy/shims/app/` | Deprecated compatibility shim. Originally a root-level `app/` package that re-exported `reliability_harness.runtime.*` and `reliability_harness.*` for backward compatibility with legacy `ReActX/test_*.py`. |
| `legacy/shims/evalforge/` | Deprecated compatibility shim. Originally a root-level `evalforge/` package that re-exported `reliability_harness.evaluation.*` for backward compatibility. |

---

## Official Entrypoints

The sole authoritative entrypoints for ReliabilityHarness experiments are:

```bash
# Official tests
bash scripts/run_tests.sh

# Official benchmark dry-run
bash scripts/run_benchmark_dry_run.sh mbpp
bash scripts/run_benchmark_dry_run.sh humaneval

# Python module
python -m reliability_harness.experiments.run_benchmark --benchmark mbpp --dry-run
python -m reliability_harness.experiments.run_benchmark --benchmark humaneval --dry-run
```

---

## Path Policy

| Purpose | Official Path |
|---------|---------------|
| Experiment outputs | `outputs/runs/`, `outputs/reports/`, `outputs/benchmark_results/` |
| Input data / fixtures | `data/tasks/`, `data/fixtures/` |
| Main package | `reliability_harness/` |

---

## Exclusion from Paper Results

Legacy materials in this directory are **excluded from paper results** unless explicitly stated.

- `legacy/ReActX/benchmark_results/` — historical data; schema predates current ReliabilityHarness pipeline. Not to be cited.
- `legacy/ReActX/runs/` — historical prototype runs; not paper results.
- `legacy/ReActX/reports/` — historical prototype reports; not paper results.
- `legacy/shims/app/` and `legacy/shims/evalforge/` — compatibility shims only; not connected to official evaluation pipeline.
