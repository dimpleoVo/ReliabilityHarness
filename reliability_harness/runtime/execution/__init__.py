"""Execution contract, runners, and integration helper — Benchmark-4A/4B/4C.

- Benchmark-4A.1: local deterministic runner (execute_locally)
- Benchmark-4B.1: Docker runner (execute_in_docker)
- Benchmark-4C.1: generation-to-execution integration helper
"""
from reliability_harness.runtime.execution.contract import ExecutionInput, ExecutionResult
from reliability_harness.runtime.execution.docker_runner import (
    DockerBackendResult,
    DockerExecutionBackend,
    execute_in_docker,
)
from reliability_harness.runtime.execution.integration import (
    ExecutionIntegrationError,
    execute_generation_artifact,
)

__all__ = [
    "ExecutionInput",
    "ExecutionResult",
    "DockerBackendResult",
    "DockerExecutionBackend",
    "execute_in_docker",
    "ExecutionIntegrationError",
    "execute_generation_artifact",
]
