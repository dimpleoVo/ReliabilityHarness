# ReliabilityHarness

**Beyond Final Success: Process-aware Reliability Evaluation for Code-generating Agents**

---

## Overview

ReliabilityHarness is a research prototype for studying the reliability behavior of code-generating agents during execution, failure, retry, and recovery.

Core idea:

> Task Success ≠ Process Correctness

Even a correct final answer may hide runtime errors, ineffective retries, unstable recovery behavior, or inconsistent tool usage. ReliabilityHarness evaluates the *process*, not just the outcome.

---

## Package Structure

The primary Python package is `reliability_harness`.

```text
reliability_harness/
├── runtime/          # Agent execution layer (agent, loop, tools, API)
├── evaluation/       # Process-aware evaluation layer
│   ├── runtime_eval/ # Evaluator, failure analyzer
│   ├── metrics/      # Metric implementations
│   ├── runner/       # Eval / benchmark / leaderboard runners
│   └── tasks/        # Task definitions
├── sandbox/          # Sandbox execution layer
├── artifacts/        # Run artifact persistence
├── reporting/        # Reliability report generation
├── reasoning/        # Trajectory analysis and reflection
├── memory/           # Memory-assisted recovery
├── core/             # Core engine and configuration
└── utils/            # Shared utilities and path helpers
```

Legacy namespace notes:
- `ReActX/` — historical implementation directory; preserved for data, tests, and benchmark results.
- `app/` and `evalforge/` at repo root — compatibility shims only; not primary entry points.

---

## Quick Start

All commands run from repo root. Set `PYTHONPATH` to the repo root.

```bash
export PYTHONPATH=$(pwd)

# Validate benchmark pipeline skeleton — no data loading, no LLM calls, no output writes
bash scripts/run_benchmark_dry_run.sh mbpp
bash scripts/run_benchmark_dry_run.sh humaneval

# Equivalent Python invocation
python -m reliability_harness.experiments.run_benchmark --benchmark mbpp --dry-run
python -m reliability_harness.experiments.run_benchmark --benchmark humaneval --dry-run

# Run official ReliabilityHarness root tests (authoritative — no ReActX)
bash scripts/run_tests.sh

# Show package info
python -m reliability_harness.cli info

# Show resolved paths
python -m reliability_harness.cli paths
```

---

## Benchmark Entrypoint

The sole authoritative entrypoint for ReliabilityHarness paper experiments is:

```bash
python -m reliability_harness.experiments.run_benchmark --benchmark <name> [--dry-run]
```

Supported benchmarks: `mbpp`, `humaneval`

**Dry-run** (validate pipeline skeleton — no data loading, no LLM calls, no output writes):

```bash
python -m reliability_harness.experiments.run_benchmark --benchmark mbpp --dry-run
python -m reliability_harness.experiments.run_benchmark --benchmark humaneval --dry-run
```

**Full run** (coming next phase — drop `--dry-run` once adapters are implemented):

```bash
python -m reliability_harness.experiments.run_benchmark --benchmark mbpp
python -m reliability_harness.experiments.run_benchmark --benchmark humaneval
```

Also accessible from the unified CLI:

```bash
python -m reliability_harness.cli benchmark --benchmark mbpp --dry-run
```

### Deprecated / Legacy entry points (not for paper results)

| Script / Entry | Status | Reason |
|---|---|---|
| `ReActX/benchmark_reliability.py` | **Deprecated** | EvalForge-era; not connected to ReliabilityHarness pipeline |
| `ReActX/evaluate.py` | **Deprecated** | Legacy EvalForge runner |
| `run_eval.py` | **Legacy** | EvalForge-style; outputs not canonical for paper |
| `scripts/legacy/run_benchmark_mock.sh` | **Legacy** | Calls run_eval.py (EvalForge-era); use `run_benchmark_dry_run.sh` instead |
| `ReActX/test_*.py` | **Legacy smoke tests** | Not constraints on new architecture; root `tests/` supersedes these. Manual legacy runs via `scripts/legacy/run_reactx_tests.sh` |
| `ReActX/benchmark_results/` | **Historical data** | Not paper results; not to be cited |
| `ReActX/runs/` | **Historical data** | Not paper results |
| `ReActX/reports/` | **Historical data** | Not paper results |

See [docs/BENCHMARK_ENTRYPOINT.md](docs/BENCHMARK_ENTRYPOINT.md) for full reference.

---

## Data and Output Paths

All paths are resolved from repo root via `reliability_harness.utils.paths` — no `os.getcwd()` dependency.

| Purpose | Path |
|---|---|
| Task fixtures | `data/tasks/` |
| Canonical dataset file | `data/reliability_tasks.json` |
| Failure memory (JSONL) | `data/failure_memory.jsonl` |
| Chroma vector DB | `data/chroma_db_data/` |
| Run artifacts | `outputs/runs/` |
| Reliability reports | `outputs/reports/` |
| Benchmark predictions | `outputs/predictions/` |
| Benchmark summaries | `outputs/benchmark_results/` |

Environment variable overrides (in priority order):

| Variable | Purpose |
|---|---|
| `RELIABILITY_HARNESS_DATASET_PATH` | Primary dataset path override |
| `DATASET_PATH` | Secondary dataset path override |
| `REACTX_DATASET_PATH` | Deprecated explicit alias — only used when explicitly set; does **not** auto-fallback to `ReActX/data/` |

See `.env.example` for a full template.

---

## Docker

All Docker configuration lives under `docker/` at repo root.
Do **not** use `ReActX/infra/docker/` — that is the legacy location.

**Static validation** (no `.env` required):

```bash
docker compose -f docker/docker-compose.yml config
```

**To run with real LLM / API calls**, create a `.env` at repo root first:

```bash
cp .env.example .env
# edit .env — set OPENAI_API_KEY and any other required values
```

**Start services:**

```bash
docker compose -f docker/docker-compose.yml up
```

Backend: `http://localhost:8000`
Sandbox: `http://localhost:9000`

Notes:
- `.env` at repo root is **optional** for static config validation; required for real API calls.
- `docker/backend.Dockerfile` uses `requirements.txt` at repo root.
- `docker/sandbox.Dockerfile` uses `docker/sandbox.requirements.txt`.
- Chroma data is mounted from `data/chroma_db_data/` at repo root into the container at `/app/data/chroma_db_data`.
- `docker/docker-compose.yml` reads `.env` from repo root (`../.env` relative to the compose file); if the file is absent, Docker Compose proceeds without it.

---

## System Architecture

```text
Task
  ↓
Memory Retrieval
  ↓
Agent Runtime  (reliability_harness.runtime)
  ↓
Code Generation
  ↓
Sandbox Execution  (reliability_harness.sandbox)
  ↓
Process-aware Evaluation  (reliability_harness.evaluation)
  ↓
Failure Analysis / Reflection / Retry
  ↓
Artifact Persistence  (reliability_harness.artifacts)
  ↓
Reliability Report  (reliability_harness.reporting)
```

---

## Key Reliability Dimensions

| Dimension | Module |
|---|---|
| Sandbox Execution | `runtime.tools`, `sandbox` |
| Failure Taxonomy | `runtime.loop.failure_taxonomy` |
| Retry Effectiveness | `runtime.loop.retry_effectiveness` |
| Tool Process Reliability | `runtime.loop.tool_process_reliability` |
| Trajectory Analysis | `reasoning.trajectory_analyzer` |
| Reflection Quality | `reasoning.reflection_evaluator` |
| Memory-assisted Recovery | `memory` |
| Artifact Persistence | `artifacts.run_artifact` |
| Reliability Reporting | `reporting.reliability_report` |

---

## Legacy Reliability Evidence Examples

> **Historical reference only.** These are ReActX-era snapshots and are **not** current ReliabilityHarness paper results. Schema and metrics predate the current `reliability_harness` evaluation pipeline.

- [Run Artifact Snapshot (legacy)](docs/legacy/examples/example_run_artifact.json)
- [Benchmark Result Snapshot (legacy)](docs/legacy/examples/example_benchmark_result.json)
- [Trajectory Analysis Snapshot (legacy)](docs/legacy/examples/example_trajectory_analysis.json)
- [Reflection Evaluation Snapshot (legacy)](docs/legacy/examples/example_reflection_evaluation.json)
- [ReActX Prototype Narrative (legacy)](docs/legacy/INTERVIEW_NARRATIVE.md)

**TODO:** Current ReliabilityHarness examples will be generated from future benchmark runs under `outputs/runs/` and `outputs/reports/` and documented separately.

---

## Project Positioning

This project is NOT:
- a production agent platform
- a general-purpose agent framework
- a scalable distributed runtime

It is:
> A lightweight research prototype for process-aware reliability evaluation of code-generating agents.

Target venue: ACL Findings / EMNLP Findings

---

## Disclaimer

Research-oriented engineering prototype. Focus is reliability experimentation, not production deployment.

Docker path and data directory simplification are ongoing; see [docs/MIGRATION_PLAN.md](docs/MIGRATION_PLAN.md).
