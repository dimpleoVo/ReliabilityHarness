"""Execution contract for Benchmark-4A.1.

Defines the input/output data shapes for code execution.
Docker-isolated execution is Benchmark-4B — this module is local-only.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ExecutionInput:
    run_id: str
    benchmark: str
    task_id: str
    candidate_code: str
    tests: list[str]
    timeout_ms: int = 1000
    docker_used: bool = False
    source_generation_artifact: Optional[str] = None


@dataclass
class ExecutionResult:
    run_id: str
    benchmark: str
    task_id: str
    exit_code: Optional[int]
    stdout: str
    stderr: str
    timed_out: bool
    tests_passed: bool
    error_type: Optional[str]
    execution_time_ms: Optional[int]
    docker_used: bool
    execution_performed: bool
