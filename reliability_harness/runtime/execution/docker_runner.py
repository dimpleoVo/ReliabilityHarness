"""Docker execution runner — Benchmark-4B.1.

Executes candidate_code + tests inside a Docker container.
Intended for agent-generated code that must not run on the host.

No LLM. No memory. No retry. No closed_loop_runner. No CodeExecutionTool.
The local_runner (Benchmark-4A.1) is unchanged by this module.

Real Docker backend requires a running Docker daemon.
Default unit tests use a mock/fake backend — no Docker daemon needed.
"""
from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from typing import Optional, Protocol, runtime_checkable

from reliability_harness.runtime.execution.contract import ExecutionInput, ExecutionResult

# ── error_type constants (mirrors local_runner constants, not imported to avoid coupling) ──
_ASSERTION_FAILURE = "assertion_failure"
_SYNTAX_ERROR = "syntax_error"
_RUNTIME_ERROR = "runtime_error"
_TIMEOUT = "timeout"
_INFRASTRUCTURE_ERROR = "infrastructure_error"
_UNKNOWN = "unknown"

# Docker image used by RealDockerBackend
_DOCKER_IMAGE = "python:3.11-slim"


# ── Backend result ─────────────────────────────────────────────────────────────

@dataclass
class DockerBackendResult:
    exit_code: Optional[int]
    stdout: str
    stderr: str
    timed_out: bool
    execution_time_ms: Optional[int]


# ── Backend protocol ───────────────────────────────────────────────────────────

@runtime_checkable
class DockerExecutionBackend(Protocol):
    def run_python(self, source_code: str, timeout_ms: int) -> DockerBackendResult:
        """Execute Python source_code and return raw backend result."""
        ...


# ── Real Docker backend ────────────────────────────────────────────────────────

class RealDockerBackend:
    """Runs source_code in a Docker container via `docker run --rm -i`.

    Requires a running Docker daemon and the python:3.11-slim image.
    Not used during default unit tests — inject a fake backend instead.
    """

    def run_python(self, source_code: str, timeout_ms: int) -> DockerBackendResult:
        timeout_s = timeout_ms / 1000.0
        start = time.monotonic()
        try:
            proc = subprocess.run(
                [
                    "docker", "run", "--rm",
                    "--network", "none",
                    "--memory", "128m",
                    "--cpus", "0.5",
                    "-i",
                    _DOCKER_IMAGE,
                    "python", "-",
                ],
                input=source_code,
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
            elapsed = int((time.monotonic() - start) * 1000)
            return DockerBackendResult(
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                timed_out=False,
                execution_time_ms=elapsed,
            )
        except subprocess.TimeoutExpired:
            elapsed = int((time.monotonic() - start) * 1000)
            return DockerBackendResult(
                exit_code=None,
                stdout="",
                stderr="",
                timed_out=True,
                execution_time_ms=elapsed,
            )


# ── Error classification ───────────────────────────────────────────────────────

def _classify_error(stderr: str) -> str:
    if not stderr:
        return _UNKNOWN
    lower = stderr.lower()
    if "assertionerror" in lower:
        return _ASSERTION_FAILURE
    if "syntaxerror" in lower:
        return _SYNTAX_ERROR
    return _RUNTIME_ERROR


def _build_source(execution_input: ExecutionInput) -> str:
    return execution_input.candidate_code.rstrip() + "\n\n" + "\n".join(execution_input.tests)


# ── Public entry point ─────────────────────────────────────────────────────────

def execute_in_docker(
    execution_input: ExecutionInput,
    backend: Optional[DockerExecutionBackend] = None,
) -> ExecutionResult:
    """Run candidate_code + tests via Docker (or injected backend).

    If backend is None, RealDockerBackend is used (requires Docker daemon).
    For unit tests, inject a fake backend — no Docker daemon needed.
    """
    if backend is None:
        backend = RealDockerBackend()

    source = _build_source(execution_input)

    try:
        bk_result = backend.run_python(source, execution_input.timeout_ms)
    except Exception as exc:
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
            execution_time_ms=None,
            docker_used=True,
            execution_performed=True,
        )

    if bk_result.timed_out:
        return ExecutionResult(
            run_id=execution_input.run_id,
            benchmark=execution_input.benchmark,
            task_id=execution_input.task_id,
            exit_code=None,
            stdout=bk_result.stdout,
            stderr=bk_result.stderr,
            timed_out=True,
            tests_passed=False,
            error_type=_TIMEOUT,
            execution_time_ms=bk_result.execution_time_ms,
            docker_used=True,
            execution_performed=True,
        )

    passed = bk_result.exit_code == 0
    error_type = None if passed else _classify_error(bk_result.stderr)

    return ExecutionResult(
        run_id=execution_input.run_id,
        benchmark=execution_input.benchmark,
        task_id=execution_input.task_id,
        exit_code=bk_result.exit_code,
        stdout=bk_result.stdout,
        stderr=bk_result.stderr,
        timed_out=False,
        tests_passed=passed,
        error_type=error_type,
        execution_time_ms=bk_result.execution_time_ms,
        docker_used=True,
        execution_performed=True,
    )
