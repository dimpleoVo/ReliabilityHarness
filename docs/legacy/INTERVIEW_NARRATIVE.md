# Interview Narrative

## 30-second Version

ReliabilityHarness is an AI Reliability Harness for code-generating agents. It focuses on whether an agent can execute safely, detect failures, retry with evidence, and preserve a structured record of what happened.

The system supports sandbox execution, evaluation-guided retry, artifact persistence, benchmark evidence, trajectory reasoning, and reflection quality evaluation. The goal is not to build a general-purpose agent framework, but to measure and improve reliability behavior around code execution.

## 2-minute Version

Task success is not the same as process correctness. A code agent can eventually print the right answer while still hitting runtime errors, timeouts, repeated failed retries, or reflection prompts that do not explain the real failure.

That is why ReliabilityHarness records attempts, generated code, stdout, stderr, runtime errors, timeout flags, reflection inputs, retry reasons, and evaluation scores. The run artifact preserves evidence instead of only storing the final answer.

The benchmark runner makes this repeatable across curated reliability tasks. It reports success rate, recovery rate, average attempts, runtime error rate, timeout rate, and category-level behavior. This gives a small but concrete way to compare reliability behavior instead of relying on one-off demos.

Trajectory reasoning adds a rule-based layer on top of the artifact. It asks whether the root cause was identified, whether retries repeated the same failure, whether reflection actually improved the run, and what type of recovery occurred. Reflection quality evaluation separately checks whether a reflection mentioned the root cause, proposed an actionable fix, or repeated the previous failure pattern.

## Key Technical Talking Points

- Sandbox timeout enforcement: generated code must run in an isolated environment with timeout and runtime error evidence preserved.
- Metric direction-aware retry effectiveness: improvement must respect whether a metric is higher-is-better or lower-is-better.
- Structured run artifacts: every run preserves attempts, code, stdout, stderr, retry reasons, and trajectory analysis.
- Reliability benchmark runner: curated reliability tasks provide repeatable evidence across runtime error, timeout, semantic error, recoverable retry, and memory-assisted categories.
- Trajectory reasoning: rule-based analysis identifies recovery type, repeated failures, reflection effectiveness, and trajectory quality.
- Reflection quality evaluation: rule-based checks determine whether a reflection explains the failure and proposes an actionable repair.

## Strongest Resume Positioning

English:

Built an AI Reliability Harness for code-generating agents with sandboxed execution, evaluation-guided retry, structured run artifacts, benchmark reporting, trajectory-level recovery analysis, and rule-based reflection quality evaluation.

中文：

构建了一个面向代码智能体的 AI Reliability Harness，支持沙箱执行、基于评测的重试修复、结构化运行证据、可靠性 benchmark、轨迹级恢复分析和 rule-based reflection 质量评估。

## Interview Questions I Should Be Ready For

1. Why is final task success insufficient for evaluating agent reliability?
2. How does the system distinguish runtime errors, timeouts, and semantic errors?
3. How do you define retry recovery?
4. How do you know a reflection fixed the root cause instead of just getting lucky?
5. What fields are stored in a run artifact, and why?
6. How does the benchmark runner avoid depending on expensive real LLM calls during tests?
7. What are the limits of rule-based trajectory reasoning?
8. How would you prevent memory-assisted retry from polluting future attempts?
9. How would you improve sandbox isolation for production use?
10. How would you compare two models using this harness?
11. What would you change before calling this production-ready?
12. How would you extend this from code agents to general tool-use agents?
