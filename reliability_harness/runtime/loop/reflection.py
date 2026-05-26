class ReflectionBuilder:
    def build(self, task, generated_code, sandbox, eval_result, strategy):
        stderr = (sandbox or {}).get("stderr", "")
        stdout = (sandbox or {}).get("stdout", "")

        if strategy == "runtime_fix":
            return self._runtime_fix(task, generated_code, stderr)

        if strategy == "semantic_fix":
            return self._semantic_fix(task, generated_code, stdout)

        return task

    def _runtime_fix(self, task, code, stderr):
        return f"""
You are a Python expert.

The following code failed with a runtime error.

Task:
{task}

Previous code:
{code}

Runtime error:
{stderr}

Fix the error and return ONLY valid Python code.
Do not explain anything.
"""

    def _semantic_fix(self, task, code, output):
        return f"""
You are a Python expert.

The code ran successfully, but the output is likely incorrect.

Task:
{task}

Previous code:
{code}

Previous output:
{output}

Fix the logic and return ONLY valid Python code.
Do not explain anything.
"""