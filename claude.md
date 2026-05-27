# ReliabilityHarness / ReActX Research Memory

## Project Positioning

This project is no longer an OCR / DocAI / edit-distance demo.

The research direction is:

**Process-aware Reliability Evaluation for Code-generating Agents**

Target venue:
**ACL Findings / EMNLP Findings level**

Primary thesis:

> Final task success does not fully reflect agent reliability.

We study agent reliability, not code generation itself. Code-generating agents are the primary testbed because code tasks provide observable execution feedback, runtime errors, test failures, retries, and reproducible artifacts.

## Core Research Objects

The project should focus on:

- reasoning consistency
- tool correctness
- retry quality
- failure recovery
- trajectory stability
- failure persistence
- reflection quality
- memory-assisted recovery

## Proposed Paper Title

Working title:

**Beyond Final Success: Process-aware Reliability Evaluation for Code-generating Agents**

## Core Contributions

1. Process-aware reliability evaluation framework
2. Failure recovery and failure persistence analysis
3. Reliability artifact / benchmark runtime
4. Optional later contribution: memory-assisted recovery

## What Must Not Be Treated as Core Anymore

The following are legacy / deprecated:

- OCR / DocAI / OmniDocBench logic
- edit_distance as primary metric
- GT-only string matching evaluation
- final-output-only evaluation
- demo-only benchmark assumptions
- mock-heavy benchmark logic

`edit_distance` may remain only as an optional auxiliary metric. It must not determine:

- task_success
- recovery_success
- retry_effectiveness
- process_reliability_score

## Benchmark Roadmap

Benchmark order:

1. MBPP
2. HumanEval
3. LiveCodeBench
4. SWE-bench Lite

Do not start with SWE-bench. SWE-bench requires repo-level patch execution and multi-tool file editing, so it is a later-stage target.

## Desired System Architecture

The system should evolve toward:

1. Dataset Adapter Layer
2. Agent Runtime Layer
3. Sandbox / Execution Layer
4. Process Evaluation Layer
5. Reliability Metrics Layer
6. Artifact / Report Layer
7. Experiment Runner Layer

## Important Current Technical Debt

Known high-priority issues:

1. `edit_distance` is still hard-coded as a primary metric.
2. `score` semantics are mixed and unreliable.
3. task success / recovery success are not cleanly separated.
4. old GT string matching logic remains in the main flow.
5. hardcoded task id such as `agent_task_001`.
6. module-level LLM initialization may break imports without API keys.
7. memory retrieval may look enabled but return empty or invalid metadata.
8. ReAct agent is currently too single-step to support meaningful trajectory analysis.
9. benchmark runner is not yet adapted for MBPP / HumanEval / LiveCodeBench / SWE-bench.
10. artifact schema needs benchmark/task/model/config fields.

## Files Known to Be Important

Likely core files (official `reliability_harness/` package):

- `reliability_harness/runtime/loop/closed_loop_runner.py`
- `reliability_harness/evaluation/`
- `reliability_harness/runtime/loop/retry_effectiveness.py`
- `reliability_harness/runtime/loop/failure_taxonomy.py`
- `reliability_harness/runtime/loop/tool_process_reliability.py`
- `reliability_harness/reasoning/trajectory_analyzer.py`
- `reliability_harness/reasoning/reflection_evaluator.py`
- `reliability_harness/artifacts/run_artifact.py`
- `reliability_harness/reporting/reliability_report.py`
- `reliability_harness/runtime/agent/react_agent.py`
- `reliability_harness/runtime/agent/trajectory.py`
- `reliability_harness/sandbox/client.py`
- `reliability_harness/sandbox/executor.py`
- `reliability_harness/memory/`
- `reliability_harness/utils/dataset_loader.py`

Archived legacy areas (moved to `legacy/` in Migration-5A — do not use as primary entrypoints):

- `legacy/shims/app/` — deprecated compatibility shim (was root-level `app/`)
- `legacy/shims/evalforge/` — deprecated compatibility shim (was root-level `evalforge/`)
- `legacy/ReActX/` — archived historical implementation
- `frontend/`
- `promoter/`

## Working Rules

When modifying code:

1. Do not make broad rewrites.
2. Do not delete legacy modules unless explicitly instructed.
3. Prefer deprecating and isolating legacy logic first.
4. Keep changes minimal, testable, and reversible.
5. Every change must include:
   - files changed
   - reason for change
   - what was not changed
   - test command
   - acceptance criteria
6. Do not introduce SWE-bench support before MBPP/HumanEval basics work.
7. Do not make memory a main contribution until retrieval correctness is verified.
8. Do not use edit_distance as primary success logic.
9. Preserve existing working tests unless the task explicitly updates them.
10. After each step, output concise implementation summary and test results.

## Current Near-term Goal

Phase 1 goal:

**Evaluation realignment**

Tasks:

1. Separate `task_success`, `final_success`, `recovery_success`, and `process_reliability`.
2. Demote `edit_distance` to auxiliary metric.
3. Remove hardcoded metric dependencies.
4. Fix task id / benchmark name propagation.
5. Prepare artifact schema for benchmark experiments.
6. Prepare MBPP/HumanEval adapter path.

Execution Policy:

默认情况下，你只能执行静态只读命令，不允许运行 Python 程序或测试。

允许默认执行：

- git status --short

- git diff --stat

- git diff --name-status

- git diff --name-only

- find

- ls

- rg

- grep

- sed -n

- cat

未经我明确授权，禁止执行：

- python

- python3

- python -m

- pytest

- python test_*.py

- python run_eval.py

- python benchmark_reliability.py

- bash scripts/run_tests.sh

- bash scripts/run_benchmark_mock.sh

- pip install

- conda install

- docker compose up

- docker build

- git add

- git commit

- git push

- git reset

- git clean

- rm -rf

例外：

如果我明确说“允许 smoke test”，你只能运行我指定的轻量命令，例如：

- python -m reliability_harness.cli info

- python -m reliability_harness.cli paths

- python -c "import reliability_harness"

即使允许 smoke test，也禁止：

- 安装依赖

- 调用 LLM/API

- 启动 Docker

- 跑 benchmark

- 跑 pytest

- 写入大量 artifact/cache

如果需要运行测试，你只列出建议命令，由我手动运行。