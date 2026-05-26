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
