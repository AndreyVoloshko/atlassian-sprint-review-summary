"""API Gateway response helpers with CORS support."""

import json

from core.config import ALLOWED_ORIGINS

_CORS_HEADERS = {
    "Access-Control-Allow-Origin": ALLOWED_ORIGINS,
    "Access-Control-Allow-Headers": "Content-Type,X-Api-Key,Authorization,X-Forge-OAuth-System",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
}


def success(body: dict) -> dict:
    return _build(200, body)


def error(status_code: int, message: str) -> dict:
    return _build(status_code, {"error": message})


def _build(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {**_CORS_HEADERS, "Content-Type": "application/json"},
        "body": json.dumps(body),
    }
