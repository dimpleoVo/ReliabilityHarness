"""
Benchmark adapter registry for ReliabilityHarness.

Usage:
    from reliability_harness.benchmarks.registry import get_adapter, list_benchmarks

    adapter = get_adapter("mbpp")        # → MBPPAdapter instance
    adapter = get_adapter("humaneval")   # → HumanEvalAdapter instance
    print(list_benchmarks())             # → ["humaneval", "mbpp"]

Design:
  - No lazy imports — all adapters are imported at module load so missing
    dependencies surface immediately, not at runtime.
  - No legacy ReActX / EvalForge imports.
  - Adding a new benchmark: register its adapter class in _REGISTRY below.
"""
from reliability_harness.benchmarks.adapters.base import BenchmarkAdapter
from reliability_harness.benchmarks.adapters.humaneval import HumanEvalAdapter
from reliability_harness.benchmarks.adapters.mbpp import MBPPAdapter
from reliability_harness.benchmarks.adapters.tiny import TinyFixtureAdapter

_REGISTRY: dict[str, type[BenchmarkAdapter]] = {
    "humaneval": HumanEvalAdapter,
    "mbpp": MBPPAdapter,
    "tiny": TinyFixtureAdapter,
}


def get_adapter(benchmark: str) -> BenchmarkAdapter:
    """Return an instantiated adapter for the given benchmark name.

    Parameters
    ----------
    benchmark:
        Case-insensitive benchmark identifier (e.g. "mbpp", "humaneval").

    Returns
    -------
    BenchmarkAdapter
        A fresh adapter instance ready for use.

    Raises
    ------
    ValueError
        If the benchmark name is not registered.
    """
    key = benchmark.lower().strip()
    if key not in _REGISTRY:
        supported = ", ".join(sorted(_REGISTRY.keys()))
        raise ValueError(
            f"Unknown benchmark: {benchmark!r}. Supported benchmarks: {supported}"
        )
    return _REGISTRY[key]()


def list_benchmarks() -> list[str]:
    """Return a sorted list of registered benchmark names."""
    return sorted(_REGISTRY.keys())
