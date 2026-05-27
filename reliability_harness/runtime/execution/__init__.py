"""Execution contract and runners — Benchmark-4A.1 / 4B.1.

- Benchmark-4A.1: local deterministic runner (execute_locally)
- Benchmark-4B.1: Docker runner (execute_in_docker)
"""
from reliability_harness.runtime.execution.contract import ExecutionInput, ExecutionResult
from reliability_harness.runtime.execution.docker_runner import (
    DockerBackendResult,
    DockerExecutionBackend,
    execute_in_docker,
)

__all__ = [
    "ExecutionInput",
    "ExecutionResult",
    "DockerBackendResult",
    "DockerExecutionBackend",
    "execute_in_docker",
]
