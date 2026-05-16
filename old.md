---

# 🔥 ReActX + EvalForge

## 🚀 LLM-driven Closed-loop Agent Evolution System

---

# 📌 Overview

**ReActX + EvalForge** is a fully functional **LLM-driven closed-loop system** that integrates:

* 🤖 Agent Execution（ReAct paradigm）
* 🧠 LLM Code Generation（DeepSeek API）
* 🧪 Sandbox Execution（Docker-isolated）
* 📊 Evaluation（EvalForge）
* 🔁 Failure-driven Retry & Reflection
* 🧠 Memory & Retrieval（Vector DB / Chroma）
* ⚖️ LLM-as-a-Judge（when no ground truth）

---

👉 The system is designed to simulate:

```text
Task
→ Agent (LLM reasoning + tool use)
→ Code Generation
→ Sandbox Execution
→ Evaluation
→ Failure Detection
→ Reflection
→ Retry
→ Memory Accumulation
→ Evolution
```

---

# 🧱 System Architecture

```
ReActX/
├── app/
│   ├── agent/            # ReAct Agent (trajectory, steps)
│   ├── tools/            # CodeExecutionTool (sandbox caller)
│   ├── loop/             # Closed-loop controller (core)
│   ├── eval/             # EvalForge + LLM Judge
│   ├── memory/           # Memory + Vector Store (Chroma)
│   └── core/             # LLM engine (DeepSeek API)
│
├── sandbox/              # Isolated execution service (Docker SDK)
│   ├── main.py
│   └── executor.py
│
├── infra/docker/         # docker-compose + Dockerfile
```

---

# ⚙️ Key Features

---

## 🔹 1. ReAct Agent (White-box Execution)

* Thought / Action / Observation fully tracked
* Supports tool calling (code_executor)
* Outputs full trajectory:

```json
{
  "thought": "...",
  "action": "...",
  "observation": "...",
  "error": "...",
  "latency": ...
}
```

👉 Enables **process-level evaluation (not just final answer)**

---

## 🔹 2. LLM Code Generation

* DeepSeek API (requests-based, UTF-8 safe)
* Code extraction + sanitization
* Fallback mechanism for robustness

---

## 🔹 3. Sandbox Execution (Production-grade)

✅ Implemented as **independent service (FastAPI, port 9000)**

* Docker SDK (NOT docker-in-docker ❗)

* Full isolation:

  * CPU / Memory limits
  * Network disabled
  * Process constraints

* Code injection via:

```text
docker.put_archive  ✅ (no shell corruption)
```

---

### 🔥 Solved critical engineering issues:

| Problem             | Solution                              |
| ------------------- | ------------------------------------- |
| docker daemon crash | Docker SDK                            |
| SIGSEGV             | remove docker-in-docker               |
| stdout loss         | file execution instead of `python -c` |
| code corruption     | put_archive instead of shell          |

---

## 🔹 4. EvalForge (Evaluation Engine)

Supports:

* edit_distance metric
* runtime_error detection
* failure summary
* slice-aware analysis
* boundary analysis

---

## 🔹 5. LLM-as-a-Judge (Core Upgrade)

When no ground truth:

```text
→ fallback to LLM Judge
```

Returns:

```json
{
  "correct": true/false,
  "reason": "..."
}
```

👉 Enables evaluation for **open-ended tasks**

---

## 🔹 6. Closed-loop Retry System

Implements:

```text
Failure → Reflection → Retry
```

---

### Reflection Prompt:

```text
The code ran but produced incorrect output.

Task: ...
Previous code: ...
Previous observation: ...

Fix the logic and return ONLY valid Python code.
```

---

## 🔹 7. Memory System (Evolution Core)

### ✅ Stored:

* task
* bad_code
* bad_output
* error_type
* fixed_code
* improvement

---

### ✅ Retrieval:

* Chroma vector DB
* top-k similar failures

---

### ✅ Injection:

```text
Solve the task.

[Memory examples]

Task: ...
```

---

👉 Enables:

```text
🔥 Failure → Learning → Avoid repeat mistakes
```

---

# 🔁 Closed-loop Execution Example

---

### Step 1 (Fail)

```text
print("helloworld")
→ wrong
```

---

### Step 2 (Fix)

```text
print("hello world")
→ correct
```

---

### Memory Saved

```json
{
  "bad_code": "print('helloworld')",
  "fixed_code": "print('hello world')"
}
```

---

### Next Run

```text
Memory Retrieved → directly correct at STEP 1
```

---

# 📊 Current Capabilities

---

## ✅ System-level

* Full closed-loop execution
* Multi-step trajectory
* Retry & reflection
* Failure-driven learning

---

## ✅ Engineering-level

* Docker sandbox (production-safe)
* Microservice architecture
* FastAPI backend
* Vector DB integration (Chroma)

---

## ✅ Evaluation-level

* Metric-based evaluation
* LLM-based evaluation
* Failure pattern mining
* Boundary analysis

---

## ✅ Behavior-level（核心亮点）

```text
✔ Self-correction
✔ Failure awareness
✔ Memory-based improvement
✔ Evolution capability
```

---

# 🧠 Key Insights (Important)

---

## 1️⃣ LLM is already strong

Simple tasks:

```text
→ solved in 1 step
```

---

## 2️⃣ Need failure-driven evaluation

We introduce:

```text
- constrained tasks
- failure injection
- retry tracking
```

---

## 3️⃣ Evaluation is control signal

Not just scoring:

```text
Eval → drives retry → drives evolution
```

---

# 🔥 Challenges Solved

---

## ⚠️ 1. Docker-in-Docker failure

→ replaced with Docker SDK

---

## ⚠️ 2. Code corruption

```text
print("hello world") → print(helloworld)
```

→ solved via `put_archive`

---

## ⚠️ 3. Encoding issues (DeepSeek)

→ replaced SDK with raw requests (UTF-8 safe)

---

## ⚠️ 4. stdout instability

→ replaced `python -c` with file execution

---

## ⚠️ 5. Evaluation gap

→ added LLM-as-a-Judge

---

# 🚀 Future Work

---

## 🔥 1. Stronger Evolution

* multi-task learning
* cross-task memory reuse

---

## 🔥 2. Better Memory Usage

* structured prompt templates
* error-type-aware retrieval

---

## 🔥 3. Dataset Construction

* auto-generated failure dataset
* benchmark creation

---

## 🔥 4. Research Direction

👉 **Failure-driven LLM Evolution**

* error → reflection → improvement
* slice-aware learning
* automated correction loops

---

# 🎯 Project Value

---

## 💼 For Interviews

This project demonstrates:

* Agent system design
* LLM integration
* Docker sandbox engineering
* evaluation system design
* failure-driven learning

---

## 📄 For Research

Potential contributions:

* evaluation-guided control loop
* failure-driven evolution
* LLM-as-a-judge integration
* memory-augmented agent systems

---

# 🧠 Final Positioning

---

This is NOT:

```text
❌ a simple agent
❌ a simple LLM wrapper
```

---

This is:

```text
🔥 An Evaluation-guided, Failure-driven LLM Evolution System
```

---

# ⭐ TL;DR

---

```text
We built a system where LLMs don’t just solve tasks,
but learn from their own failures and improve over time.
```
