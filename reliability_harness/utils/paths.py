"""Path helpers for ReliabilityHarness.

All paths are derived from __file__ so they work regardless of cwd.
"""
from pathlib import Path
import os

# reliability_harness/utils/paths.py  ->  .parent.parent = reliability_harness/  ->  .parent = repo root
PACKAGE_ROOT: Path = Path(__file__).resolve().parent.parent
REPO_ROOT: Path = PACKAGE_ROOT.parent

CONFIGS_ROOT: Path = REPO_ROOT / "configs"
DOCS_ROOT: Path = REPO_ROOT / "docs"
SCRIPTS_ROOT: Path = REPO_ROOT / "scripts"
LEGACY_REACTX_ROOT: Path = REPO_ROOT / "ReActX"

# ── Input data (canonical locations) ─────────────────────────────────────────
DATA_ROOT: Path = REPO_ROOT / "data"
TASKS_ROOT: Path = DATA_ROOT / "tasks"
CHROMA_DB_ROOT: Path = DATA_ROOT / "chroma_db_data"
FAILURE_MEMORY_PATH: Path = DATA_ROOT / "failure_memory.jsonl"

# ── Generated outputs ─────────────────────────────────────────────────────────
OUTPUTS_ROOT: Path = REPO_ROOT / "outputs"
RUNS_ROOT: Path = OUTPUTS_ROOT / "runs"
REPORTS_ROOT: Path = OUTPUTS_ROOT / "reports"
PREDICTIONS_ROOT: Path = OUTPUTS_ROOT / "predictions"
BENCHMARK_RESULTS_ROOT: Path = OUTPUTS_ROOT / "benchmark_results"
ARTIFACTS_ROOT: Path = OUTPUTS_ROOT / "artifacts"


def repo_path(*parts: str) -> Path:
    return REPO_ROOT.joinpath(*parts)


def package_path(*parts: str) -> Path:
    return PACKAGE_ROOT.joinpath(*parts)


def config_path(*parts: str) -> Path:
    return CONFIGS_ROOT.joinpath(*parts)


def artifact_path(*parts: str) -> Path:
    return ARTIFACTS_ROOT.joinpath(*parts)


def report_path(*parts: str) -> Path:
    return REPORTS_ROOT.joinpath(*parts)


def data_path(*parts: str) -> Path:
    return DATA_ROOT.joinpath(*parts)


def tasks_path(*parts: str) -> Path:
    return TASKS_ROOT.joinpath(*parts)


def failure_memory_path() -> Path:
    return FAILURE_MEMORY_PATH


def runs_path(*parts: str) -> Path:
    return RUNS_ROOT.joinpath(*parts)


def reports_path(*parts: str) -> Path:
    return REPORTS_ROOT.joinpath(*parts)


def predictions_path(*parts: str) -> Path:
    return PREDICTIONS_ROOT.joinpath(*parts)


def benchmark_results_path(*parts: str) -> Path:
    return BENCHMARK_RESULTS_ROOT.joinpath(*parts)


def chroma_path(*parts: str) -> Path:
    return CHROMA_DB_ROOT.joinpath(*parts)


def outputs_path(*parts: str) -> Path:
    return OUTPUTS_ROOT.joinpath(*parts)


def resolve_path(path: str, base: str = "repo") -> Path:
    bases = {
        "repo": REPO_ROOT,
        "package": PACKAGE_ROOT,
        "configs": CONFIGS_ROOT,
        "data": DATA_ROOT,
        "runs": RUNS_ROOT,
        "reports": REPORTS_ROOT,
        "outputs": OUTPUTS_ROOT,
        "artifacts": ARTIFACTS_ROOT,
    }
    return bases.get(base, REPO_ROOT) / path


def get_pythonpath() -> str:
    return str(REPO_ROOT)


def get_docker_compose_file() -> Path:
    return REPO_ROOT / "docker" / "docker-compose.yml"


def get_backend_dockerfile() -> Path:
    return REPO_ROOT / "docker" / "backend.Dockerfile"


def get_sandbox_dockerfile() -> Path:
    return REPO_ROOT / "docker" / "sandbox.Dockerfile"
