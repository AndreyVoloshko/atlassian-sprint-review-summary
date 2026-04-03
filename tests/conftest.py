import os

import pytest

os.environ.setdefault("BEDROCK_MODEL_ID", "eu.amazon.nova-micro-v1:0")
os.environ.setdefault("BEDROCK_REGION", "eu-central-1")
os.environ.setdefault("BEDROCK_MAX_TOKENS", "2048")
os.environ.setdefault("BEDROCK_TEMPERATURE", "0.3")
os.environ.setdefault("BEDROCK_TOP_P", "0.9")
os.environ.setdefault("AUTH_MODE", "none")
os.environ.setdefault("FORGE_APP_ID", "")
os.environ.setdefault("ALLOWED_ORIGINS", "*")
os.environ.setdefault("LOG_LEVEL", "DEBUG")


@pytest.fixture()
def api_event():
    """Factory for API Gateway proxy events."""
    def _make(method: str = "POST", path: str = "/summarize", body: str | None = None, headers: dict | None = None):
        return {
            "httpMethod": method,
            "path": path,
            "headers": headers or {"Content-Type": "application/json"},
            "body": body,
        }
    return _make
