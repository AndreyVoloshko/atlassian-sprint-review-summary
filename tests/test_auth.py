import time

from urllib.error import URLError

from auth import forge_jwt
from auth.forge_jwt import validate_request


def test_none_mode_passes(monkeypatch):
    monkeypatch.setattr("auth.forge_jwt.AUTH_MODE", "none")
    assert validate_request({"headers": {}}) is None


def test_api_key_mode_passes(monkeypatch):
    monkeypatch.setattr("auth.forge_jwt.AUTH_MODE", "api-key")
    assert validate_request({"headers": {}}) is None


def test_forge_jwt_missing_token(monkeypatch):
    monkeypatch.setattr("auth.forge_jwt.AUTH_MODE", "forge-jwt")
    result = validate_request({"headers": {}})
    assert result == "Missing authentication token"


def test_forge_jwt_invalid_token(monkeypatch):
    monkeypatch.setattr("auth.forge_jwt.AUTH_MODE", "forge-jwt")
    event = {"headers": {"Authorization": "Bearer bad.token.here"}}
    result = validate_request(event)
    assert result is not None
    assert "token" in result.lower() or "auth" in result.lower()


def test_jwks_stale_cache_fallback_on_network_error(monkeypatch):
    now = time.time()
    monkeypatch.setattr("auth.forge_jwt._jwks_cache", {"keys": [{"kid": "cached"}]})
    monkeypatch.setattr("auth.forge_jwt._jwks_cache_time", now - forge_jwt._JWKS_CACHE_TTL - 1)

    def _raise(*args, **kwargs):
        raise URLError("temporary DNS issue")

    monkeypatch.setattr("urllib.request.urlopen", _raise)
    result = forge_jwt._get_forge_jwks()
    assert result["keys"][0]["kid"] == "cached"
