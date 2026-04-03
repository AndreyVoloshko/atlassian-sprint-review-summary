"""Centralized configuration loaded from root config.yaml with env overrides."""

import os
from pathlib import Path
from typing import Any

import yaml


def _find_config_path() -> Path:
    """Find config.yaml in Lambda artifact root or local project root."""
    here = Path(__file__).resolve()
    # In Lambda artifact layout, core/config.py -> /var/task/core/config.py
    # so parent.parent is /var/task where config.yaml is copied by Makefile.
    immediate_candidate = here.parent.parent / "config.yaml"
    if immediate_candidate.exists():
        return immediate_candidate

    # Local development/tests: walk upwards until project root is found.
    for parent in here.parents:
        candidate = parent / "config.yaml"
        if candidate.exists():
            return candidate

    raise FileNotFoundError("config.yaml not found. Expected at Lambda artifact root or project root.")


def _load_root_config() -> dict[str, Any]:
    config_path = _find_config_path()
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _coerce_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _coerce_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


_ROOT_CONFIG = _load_root_config()

MODEL_CONFIG: dict[str, Any] = _ROOT_CONFIG.get("model", {})
AUTH_CONFIG: dict[str, Any] = _ROOT_CONFIG.get("auth", {})
API_CONFIG: dict[str, Any] = _ROOT_CONFIG.get("api", {})
PROMPT_CONFIG: dict[str, Any] = _ROOT_CONFIG.get("prompt", {})


BEDROCK_MODEL_ID: str = os.environ.get("BEDROCK_MODEL_ID") or MODEL_CONFIG.get("id", "eu.amazon.nova-micro-v1:0")
BEDROCK_REGION: str = os.environ.get("BEDROCK_REGION") or MODEL_CONFIG.get("region", "eu-central-1")
BEDROCK_MAX_TOKENS: int = _coerce_int(
    os.environ.get("BEDROCK_MAX_TOKENS", MODEL_CONFIG.get("max_tokens", 2048)),
    2048,
)
BEDROCK_TEMPERATURE: float = _coerce_float(
    os.environ.get("BEDROCK_TEMPERATURE", MODEL_CONFIG.get("temperature", 0.3)),
    0.3,
)
BEDROCK_TOP_P: float = _coerce_float(
    os.environ.get("BEDROCK_TOP_P", MODEL_CONFIG.get("top_p", 0.9)),
    0.9,
)

AUTH_MODE: str = os.environ.get("AUTH_MODE") or AUTH_CONFIG.get("mode", "forge-jwt")
FORGE_APP_ID: str = os.environ.get("FORGE_APP_ID") or AUTH_CONFIG.get("forge_app_id", "")

ALLOWED_ORIGINS: str = os.environ.get("ALLOWED_ORIGINS") or API_CONFIG.get("allowed_origins", "*")
LOG_LEVEL: str = os.environ.get("LOG_LEVEL") or API_CONFIG.get("log_level", "INFO")
