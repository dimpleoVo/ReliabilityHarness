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
OUTPUTS_ROOT: Path = REPO_ROOT / "outputs"
ARTIFACTS_ROOT: Path = OUTPUTS_ROOT / "artifacts"
REPORTS_ROOT: Path = OUTPUTS_ROOT / "reports"
LEGACY_REACTX_ROOT: Path = REPO_ROOT / "ReActX"

# Runtime data roots (canonical locations after full migration)
DATA_ROOT: Path = REPO_ROOT / "data"
RUNS_ROOT: Path = REPO_ROOT / "runs"
CHROMA_DB_ROOT: Path = DATA_ROOT / "chroma_db_data"


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


def runs_path(*parts: str) -> Path:
    return RUNS_ROOT.joinpath(*parts)


def chroma_path(*parts: str) -> Path:
    return CHROMA_DB_ROOT.joinpath(*parts)


def outputs_path(*parts: str) -> Path:
    return OUTPUTS_ROOT.joinpath(*parts)


def resolve_path(path: str, base: str = "repo") -> Path:
    bases = {
        "repo": REPO_ROOT,
        "package": PACKAGE_ROOT,
        "configs": CONFIGS_ROOT,
        "artifacts": ARTIFACTS_ROOT,
        "reports": REPORTS_ROOT,
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
