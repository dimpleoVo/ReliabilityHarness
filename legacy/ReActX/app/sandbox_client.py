import os
import requests


class SandboxClient:
    def __init__(self, base_url: str | None = None):
        # SANDBOX_URL (engine convention) takes precedence over SANDBOX_BASE_URL
        self.base_url = (
            base_url
            or os.getenv("SANDBOX_URL")
            or os.getenv("SANDBOX_BASE_URL", "http://sandbox:9000")
        ).rstrip("/")

    def execute_python(self, code: str, timeout: int = 10, image: str = "python:3.11-slim") -> dict:
        """
        Returns a dict always containing:
          status, stdout, stderr, return_code, timeout, runtime_error, runtime
        Never raises — HTTP errors are returned as a structured error dict.
        """
        try:
            resp = requests.post(
                f"{self.base_url}/execute",
                json={"code": code, "timeout": timeout, "image": image},
                timeout=timeout + 5,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.HTTPError as e:
            return {
                "status": "error",
                "stdout": "",
                "stderr": str(e),
                "return_code": 1,
                "timeout": False,
                "runtime_error": True,
                "runtime": 0.0,
            }
        except Exception as e:
            return {
                "status": "error",
                "stdout": "",
                "stderr": str(e),
                "return_code": 1,
                "timeout": False,
                "runtime_error": True,
                "runtime": 0.0,
            }