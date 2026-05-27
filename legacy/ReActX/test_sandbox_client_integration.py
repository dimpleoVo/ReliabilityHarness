"""
Tests for SandboxClient field passthrough and engine.py migration.
No Docker, no network — patches requests.post via unittest.mock.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import json
from unittest.mock import patch, MagicMock
import requests as _requests

from app.sandbox_client import SandboxClient

REQUIRED_FIELDS = {"status", "stdout", "stderr", "return_code", "timeout", "runtime_error", "runtime"}


def _mock_resp(payload: dict, status_code: int = 200) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = payload
    mock.text = json.dumps(payload)
    if status_code >= 400:
        mock.raise_for_status.side_effect = _requests.HTTPError(f"HTTP {status_code}")
    else:
        mock.raise_for_status.return_value = None
    return mock


def test_normal_execution_passthrough():
    payload = {
        "status": "success",
        "stdout": "42\n",
        "stderr": "",
        "return_code": 0,
        "timeout": False,
        "runtime_error": False,
        "runtime": 0.123,
    }
    with patch("requests.post", return_value=_mock_resp(payload)):
        result = SandboxClient(base_url="http://mock:9000").execute_python("print(42)")
    assert result["stdout"] == "42\n"
    assert result["timeout"] is False
    assert result["runtime_error"] is False
    assert result["return_code"] == 0
    assert REQUIRED_FIELDS <= set(result.keys()), f"Missing: {REQUIRED_FIELDS - set(result.keys())}"


def test_timeout_passthrough():
    payload = {
        "status": "error",
        "stdout": "",
        "stderr": "Execution timed out after 10s",
        "return_code": 124,
        "timeout": True,
        "runtime_error": True,
        "runtime": 10.01,
    }
    with patch("requests.post", return_value=_mock_resp(payload)):
        result = SandboxClient(base_url="http://mock:9000").execute_python("while True: pass", timeout=10)
    assert result["timeout"] is True
    assert result["runtime_error"] is True
    assert result["return_code"] == 124
    assert REQUIRED_FIELDS <= set(result.keys())


def test_http_error_returns_structured_dict():
    with patch("requests.post", return_value=_mock_resp({}, status_code=500)):
        result = SandboxClient(base_url="http://mock:9000").execute_python("print(1)")
    assert result["status"] == "error"
    assert result["runtime_error"] is True
    assert REQUIRED_FIELDS <= set(result.keys()), f"Missing: {REQUIRED_FIELDS - set(result.keys())}"


def test_network_error_returns_structured_dict():
    with patch("requests.post", side_effect=ConnectionError("refused")):
        result = SandboxClient(base_url="http://mock:9000").execute_python("print(1)")
    assert result["status"] == "error"
    assert result["runtime_error"] is True
    assert REQUIRED_FIELDS <= set(result.keys())


def test_env_var_sandbox_url_takes_precedence(monkeypatch=None):
    import os as _os
    old = _os.environ.copy()
    _os.environ["SANDBOX_URL"] = "http://from-env:9000"
    _os.environ.pop("SANDBOX_BASE_URL", None)
    try:
        client = SandboxClient()
        assert client.base_url == "http://from-env:9000", f"Got: {client.base_url}"
    finally:
        _os.environ.clear()
        _os.environ.update(old)


def test_engine_no_longer_uses_raw_requests():
    engine_path = os.path.join(os.path.dirname(__file__), "app", "core", "engine.py")
    with open(engine_path) as f:
        source = f.read()
    assert "requests.post" not in source, (
        "engine.py still contains requests.post — sandbox call not fully migrated"
    )
    assert "SandboxClient" in source, (
        "engine.py does not import or use SandboxClient"
    )
    assert "import requests" not in source, (
        "engine.py still imports requests directly"
    )


if __name__ == "__main__":
    tests = [
        test_normal_execution_passthrough,
        test_timeout_passthrough,
        test_http_error_returns_structured_dict,
        test_network_error_returns_structured_dict,
        test_env_var_sandbox_url_takes_precedence,
        test_engine_no_longer_uses_raw_requests,
    ]
    passed = failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS  {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL  {test.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    if failed:
        sys.exit(1)
