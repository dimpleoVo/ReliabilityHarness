import os
import requests


class SandboxClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or os.getenv("SANDBOX_BASE_URL", "http://sandbox:9000")

    def execute_python(self, code: str, timeout: int = 10, image: str = "python:3.11-slim") -> dict:
        resp = requests.post(
            f"{self.base_url}/execute",
            json={
                "code": code,
                "timeout": timeout,
                "image": image,
            },
            timeout=timeout + 5,
        )
        resp.raise_for_status()
        return resp.json()