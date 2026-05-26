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

# Show package info
python -m reliability_harness.cli info

# Show resolved paths
python -m reliability_harness.cli paths

# Run tests
bash scripts/run_tests.sh

# Run mock benchmark
bash scripts/run_benchmark_mock.sh
```

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
- Chroma data is mounted from `chroma_db/` at repo root into the container at `/app/data/chroma_db_data`.
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

## Reliability Evidence Examples

- [Run Artifact Example](ReActX/docs/examples/example_run_artifact.json)
- [Benchmark Result Example](ReActX/docs/examples/example_benchmark_result.json)
- [Trajectory Analysis Example](ReActX/docs/examples/example_trajectory_analysis.json)
- [Reflection Evaluation Example](ReActX/docs/examples/example_reflection_evaluation.json)
- [Interview Narrative](ReActX/docs/INTERVIEW_NARRATIVE.md)

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
