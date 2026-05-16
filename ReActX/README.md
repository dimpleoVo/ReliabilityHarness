ReActX — AI Reliability Detection & Self-Healing Harness

Overview

ReActX is an evaluation-driven closed-loop Agent reliability system for LLM-based code generation.

Instead of only generating and executing code, ReActX focuses on:

* detecting reliability failures during Agent execution
* evaluating execution correctness and process quality
* retrying failed executions through reflection
* recording failure-repair experiences
* improving future executions using memory retrieval

The system combines:

* ReActX → Agent runtime and execution loop
* EvalForge → evaluation, failure attribution, and reliability analysis
* Docker Sandbox → isolated code execution
* Failure Memory + Chroma → retrieval-enhanced repair optimization

The project is designed as a lightweight:

AI Reliability Detection & Self-Healing Harness

for Code Agents and future Tool-use / Workflow Agents.

⸻

Why AI Reliability Detection

Modern LLM Agents frequently fail in real execution environments.

Typical failure modes include:

* runtime exceptions
* hallucinated observations
* malformed tool outputs
* retry collapse
* memory pollution
* workflow inconsistency
* sandbox execution failures
* observation mismatch

ReActX is designed to detect, classify, replay, and optimize these failures.

The project focuses on:

* execution reliability
* process reliability
* retry effectiveness
* tool reliability
* memory-guided repair
* trace observability
* failure attribution

rather than only final-answer benchmarking.

⸻

System Architecture

User / Frontend
    ↓
FastAPI Backend
    ↓
run_closed_loop()
    ↓
ReActXAgent
    ↓
CodeExecutionTool
    ↓
X_Service (LLM Code Generation)
    ↓
Docker Sandbox Execution
    ↓
EvalForge Evaluation
    ↓
Failure Taxonomy
    ↓
Reflection Retry
    ↓
Failure Memory Retrieval / Save
    ↓
Reliability Report + Trace Replay

⸻

Core Reliability Pipeline

Task
→ Agent Execution
→ Code Generation
→ Sandbox Execution
→ Evaluation
→ Failure Attribution
→ Reflection
→ Retry
→ Reliability Analysis
→ Memory Save
→ Future Retrieval Optimization

⸻

Main Features

1. Closed-loop Agent Runtime

ReActX supports an evaluation-driven execution loop:

* execute task
* evaluate result
* detect failures
* generate reflection
* retry automatically
* store successful recovery experience

Core entry:

ReActX/app/loop/closed_loop_runner.py

⸻

2. Docker Sandbox Execution

Generated Python code runs inside isolated Docker containers.

Features:

* isolated execution environment
* stdout / stderr capture
* runtime error detection
* return_code tracking
* tar-stream file injection
* sandbox reliability analysis

Sandbox endpoint:

POST http://localhost:9000/execute

⸻

3. Reliability Detection

The system detects multiple reliability failure types:

Execution Reliability

* syntax_error
* runtime_exception
* timeout
* sandbox_http_error
* empty_output

Process Reliability

* observation_mismatch
* missing_tool_signal
* malformed_step
* retry_failure

Memory Reliability

* stale_memory
* memory_pollution_risk
* irrelevant_failure_fix_examples

⸻

4. Trajectory Observability

Each Agent step records:

thought
action
tool
tool_input
observation
error
latency
generated_code
sandbox

Trajectory steps are attached to EvalForge meta for:

* process-level evaluation
* reliability replay
* failure attribution
* trace analysis

⸻

5. EvalForge Reliability Evaluation

EvalForge provides:

* metric evaluation
* LLM Judge fallback
* invalid output detection
* failure taxonomy
* weak slice analysis
* risk region analysis
* badcase analysis

Current success evaluation logic includes:

* runtime error detection
* edit distance threshold
* LLM Judge confidence
* retry recovery status

⸻

6. Reflection Retry

If execution fails:

Failure
→ Reflection Prompt
→ Retry Generation
→ Re-evaluation

The retry controller supports:

* multi-step retry
* retry effectiveness analysis
* score_before / score_after comparison
* recovery detection

⸻

7. Failure Memory Retrieval

ReActX stores failure-repair examples:

Task
Bad Code
Error
Fixed Code
Fixed Output
Score Improvement

Memory is retrieved using Chroma vector search and injected into future prompts.

Example:

=== Similar Past Failure-Fix Examples ===
Task:
similar task minimal memory verification
Bad Code:
print(1 / 0)
Error:
ZeroDivisionError: division by zero
Fixed Code:
print(0)

The system also includes a memory guard to reduce memory pollution risks.

⸻

8. Reliability Report

Each closed-loop execution now produces:

* reliability_report
* reliability_events
* tool_reliability
* retry_effectiveness
* coding_metrics
* tool_process_reliability
* failure_taxonomy

These outputs summarize:

* whether the task succeeded
* whether retry recovered failure
* whether memory was used
* runtime error statistics
* process reliability quality
* tool execution consistency

⸻

9. Trace Replay

The system supports execution replay using:

replay_trace(result)

Replay output includes:

* Reliability Summary
* Attempt Timeline
* Generated Code
* Sandbox Result
* Reliability Events
* Failure Taxonomy
* Retry Effectiveness

⸻

API Endpoints

Backend Health Check

GET http://localhost:8000/health

Run Agent

POST http://localhost:8000/v1/agent/run

Example:

{
  "query": "Write Python code that prints 42."
  "history": []
}

Sandbox Health Check

GET http://localhost:9000/health

Sandbox Execution

POST http://localhost:9000/execute

⸻

Project Structure

ReActX/
├── app/
│   ├── agent/
│   ├── core/
│   ├── loop/
│   ├── memory/
│   └── main_api.py
├── evalforge/
├── sandbox/
├── frontend/
├── infra/
├── tests/
└── data/

⸻

Current Implemented Capabilities

Implemented and verified:

* DeepSeek-based code generation
* Docker sandbox execution
* trajectory logging
* EvalForge evaluation adapter
* reflection retry
* failure memory retrieval
* Chroma integration
* reliability report generation
* failure taxonomy
* retry effectiveness analysis
* trace replay
* process-level trajectory meta injection

⸻

Current Limitations

Current system limitations:

* ReActXAgent is currently a single-step code execution agent
* multi-tool orchestration is still limited
* full workflow reliability analysis is not finished
* some tests require environment dependencies:
    * DEEPSEEK_API_KEY
    * chromadb
* README was previously corrupted and rebuilt
* some legacy evaluation modules were removed during migration

⸻

Future Improvements

Planned future upgrades:

* multi-tool Agent runtime
* Browser / Search / File tools
* workflow-level reliability evaluation
* memory quality scoring
* long-running Agent support
* async task scheduling
* distributed reliability tracing
* online evaluation dashboard
* reliability benchmark suite

⸻

Technology Stack

* Python
* FastAPI
* Docker SDK
* ChromaDB
* httpx
* LangChain
* Streamlit

⸻

Vision

ReActX is not only a code-generation Agent project.

The long-term goal is:

building reliable, observable, self-healing AI execution systems.

The project explores how LLM-based Agents can:

* execute safely
* recover from failures
* improve from experience
* expose reliability signals
* support process-level evaluation
* evolve through evaluation-driven optimization