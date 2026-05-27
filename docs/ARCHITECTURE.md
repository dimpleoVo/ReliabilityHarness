# ReliabilityHarness — Architecture

## Package: `reliability_harness`

The system is organized into seven layers. Each layer has a dedicated subpackage.

---

## Layer 1: Runtime Execution Layer

**Package:** `reliability_harness.runtime`

Handles agent execution, tool dispatch, closed-loop retry, and the evaluation-guided loop.

Submodules:
- `runtime.agent` — ReAct agent, trajectory, state, tools registry
- `runtime.loop` — closed loop runner, retry controller, failure taxonomy, coding metrics, eval adapter
- `runtime.tools` — code executor, evaluator tool, base tools
- `runtime.api` — FastAPI routes
- `runtime.service` — evaluation, execution, task services
- `runtime.feedback` — failure-to-prompt, regression builder
- `runtime.schemas` — action, eval, feedback, task, trajectory schemas
- `runtime.main_api` — FastAPI application entrypoint

---

## Layer 2: Process-aware Evaluation Layer

**Package:** `reliability_harness.evaluation`

Evaluates agent behavior at the process level, not just final output.

Submodules:
- `evaluation.runtime_eval` — Evaluator, FailureAnalyzer, LLM judge, boundary analyzer
- `evaluation.metrics` — metric registry, edit distance (auxiliary), LLM judge, task success, tool success
- `evaluation.runner` — eval runner, benchmark runner, leaderboard runner, prediction runner
- `evaluation.tasks` — task registry, base task, agent task, QA task, recognition task
- `evaluation.model_registry` — model runner registry, Docker runner, OpenAI-compat runner
- `evaluation.analysis` — failure discovery, weak slices, error patterns, badcase mining
- `evaluation.datasets` — dataset registry, loaders
- `evaluation.reports` — report generator, badcase debugger, leaderboard report
- `evaluation.scheduler` — parallel scheduler
- `evaluation.utils` — YAML loading, file utilities

---

## Layer 3: Sandbox Execution Layer

**Package:** `reliability_harness.sandbox`

Provides Docker-isolated code execution.

Submodules:
- `sandbox.executor` — DockerSandboxExecutor (runs code in containers)
- `sandbox.main` — FastAPI sandbox service (uvicorn at port 9000)
- `sandbox.client` — SandboxClient (HTTP client for the sandbox service)

---

## Layer 4: Artifact / Reporting Layer

**Package:** `reliability_harness.artifacts`, `reliability_harness.reporting`

Persists structured execution traces and generates reliability reports.

Submodules:
- `artifacts.run_artifact` — save and load run artifact JSON
- `reporting.reliability_report` — aggregate metrics, generate markdown/JSON reports

---

## Layer 5: Reasoning Layer

**Package:** `reliability_harness.reasoning`

Analyzes trajectory quality and reflection effectiveness.

Submodules:
- `reasoning.trajectory_analyzer` — step-level trajectory analysis
- `reasoning.reflection_evaluator` — reflection quality scoring

---

## Layer 6: Memory / Recovery Layer

**Package:** `reliability_harness.memory`

Stores and retrieves failure memories for recovery-guided retry.

Submodules:
- `memory.store` — FailureMemoryStore
- `memory.retriever` — FailureMemoryRetriever
- `memory.vector_store` — FailureMemoryVectorStore (Chroma-backed)
- `memory.prompt_memory` — MemoryPromptBuilder
- `memory.schema` — FailureMemoryItem schema

---

## Layer 7: Core Layer

**Package:** `reliability_harness.core`

Shared engine, LLM client, RAG, configuration, and code sanitizer.

Submodules:
- `core.engine` — ELE_Service
- `core.llm` — LLM service wrapper
- `core.rag` — RAG engine
- `core.config` — configuration loading
- `core.code_sanitizer` — CodeSanitizer
- `core.logging` — logging setup

---

## Layer 8: Benchmarks Layer

**Package:** `reliability_harness.benchmarks`, `reliability_harness.experiments`

Adapter-based benchmark integration and experiment runner for paper evaluations.

Submodules:
- `benchmarks.task_schema` — `BenchmarkTask` dataclass (canonical schema between adapter and runtime)
- `benchmarks.adapters.base` — `BenchmarkAdapter` ABC (`load_tasks()`, `normalize()`)
- `benchmarks.adapters.mbpp` — MBPP adapter (stub; full implementation in next phase)
- `benchmarks.adapters.humaneval` — HumanEval adapter (stub; full implementation in next phase)
- `benchmarks.registry` — `get_adapter()` and `list_benchmarks()` dispatch
- `experiments.run_benchmark` — sole authoritative entrypoint for paper benchmark runs

**Paper entrypoint:**

```bash
python -m reliability_harness.experiments.run_benchmark --benchmark <name> [--dry-run]
```

Supported benchmarks: `mbpp`, `humaneval`

**Benchmark roadmap:** MBPP → HumanEval → LiveCodeBench → SWE-bench Lite

---

## Current Migration Status

| Phase | Status |
|---|---|
| Migration-1: reliability_harness package creation | Completed |
| Migration-2A: Docker / runtime path stabilization | Completed |
| Migration-2B-1: Unified data/output paths | Completed |
| Benchmark-0: Benchmark adapter skeleton + experiment entrypoint | Completed |
| **Migration-4A/B: Official entrypoint cleanup + root tests** | **In progress** |
| Migration-2B-2: Physical data migration | Planned |
| Migration-3: Test migration and legacy cleanup | Planned |
| Migration-4 (full): MBPP/HumanEval adapter implementation | Planned |

**Migration-4A/B adds:**
- `scripts/run_benchmark_dry_run.sh` — official shell entrypoint for dry-run validation.
- `tests/test_benchmark_entrypoint.py`, `tests/test_benchmark_registry.py`, `tests/test_benchmark_task_schema.py` — root-level tests that are the authoritative constraints on the Benchmark-0 skeleton. These supersede `ReActX/test_*.py` for new-architecture concerns.
- `ReActX/test_*.py` are preserved but are NOT constraints on `reliability_harness.*` behavior.

---

## Compatibility Namespaces

The following are **shim-only** namespaces at repo root. They redirect imports to `reliability_harness.*` and must not be used as primary entry points in new code.

- `app/` → shims to `reliability_harness.runtime.*` and `reliability_harness.*`
- `evalforge/` → shims to `reliability_harness.evaluation.*`

Legacy data and test directories (`ReActX/data/`, `ReActX/benchmark_results/`, `ReActX/test_*.py`) are preserved in `ReActX/` and will be migrated in a later phase.

---

## Docker

- `docker/backend.Dockerfile` — backend service (`reliability_harness.runtime.main_api:app`)
- `docker/sandbox.Dockerfile` — sandbox service (`reliability_harness.sandbox.main:app`)
- `docker/docker-compose.yml` — orchestration (PYTHONPATH=/app, working_dir=/app)
