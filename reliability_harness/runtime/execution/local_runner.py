"""Local deterministic runner — Benchmark-4A.1.

Executes candidate_code + test assertions in a subprocess.
ONLY intended for controlled contract tests with trusted fixture code.
Agent-generated code execution must use Docker isolation (Benchmark-4B).

No Docker. No LLM. No memory. No retry. No sandbox client.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path

from reliability_harness.runtime.execution.contract import ExecutionInput, ExecutionResult

# error_type constants
_ASSERTION_FAILURE = "assertion_failure"
_SYNTAX_ERROR = "syntax_error"
_RUNTIME_ERROR = "runtime_error"
_TIMEOUT = "timeout"
_INFRASTRUCTURE_ERROR = "infrastructure_error"
_UNKNOWN = "unknown"


def _classify_error(stderr: str, exit_code: int | None) -> str:
    if not stderr:
        return _UNKNOWN
    lower = stderr.lower()
    if "assertionerror" in lower:
        return _ASSERTION_FAILURE
    if "syntaxerror" in lower:
        return _SYNTAX_ERROR
    return _RUNTIME_ERROR


def execute_locally(execution_input: ExecutionInput) -> ExecutionResult:
    """Run candidate_code + tests in a subprocess. Returns ExecutionResult.

    Only for controlled Benchmark-4A.1 contract tests with trusted fixture code.
    """
    combined = execution_input.candidate_code.rstrip() + "\n\n"
    combined += "\n".join(execution_input.tests)

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        prefix="rh_exec_",
        delete=False,
        encoding="utf-8",
    ) as tmp:
        tmp.write(combined)
        tmp_path = tmp.name

    timeout_s = execution_input.timeout_ms / 1000.0
    start = time.monotonic()

    try:
        proc = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        elapsed = int((time.monotonic() - start) * 1000)
        Path(tmp_path).unlink(missing_ok=True)
        return ExecutionResult(
            run_id=execution_input.run_id,
            benchmark=execution_input.benchmark,
            task_id=execution_input.task_id,
            exit_code=None,
            stdout="",
            stderr="",
            timed_out=True,
            tests_passed=False,
            error_type=_TIMEOUT,
            execution_time_ms=elapsed,
            docker_used=False,
            execution_performed=True,
        )
    except Exception as exc:
        elapsed = int((time.monotonic() - start) * 1000)
        Path(tmp_path).unlink(missing_ok=True)
        return ExecutionResult(
            run_id=execution_input.run_id,
            benchmark=execution_input.benchmark,
            task_id=execution_input.task_id,
            exit_code=None,
            stdout="",
            stderr=str(exc),
            timed_out=False,
            tests_passed=False,
            error_type=_INFRASTRUCTURE_ERROR,
            execution_time_ms=elapsed,
            docker_used=False,
            execution_performed=True,
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    elapsed = int((time.monotonic() - start) * 1000)
    passed = proc.returncode == 0

    if passed:
        error_type = None
    else:
        error_type = _classify_error(proc.stderr, proc.returncode)

    return ExecutionResult(
        run_id=execution_input.run_id,
        benchmark=execution_input.benchmark,
        task_id=execution_input.task_id,
        exit_code=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        timed_out=False,
        tests_passed=passed,
        error_type=error_type,
        execution_time_ms=elapsed,
        docker_used=False,
        execution_performed=True,
    )
