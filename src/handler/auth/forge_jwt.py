"""Atlassian Forge JWT validation against the public JWKS endpoint."""

import json
import logging
import time
from urllib.error import HTTPError, URLError
import urllib.request

import jwt

from core.config import AUTH_MODE, FORGE_APP_ID

logger = logging.getLogger(__name__)

# Forge Remote FIT validation settings (official docs/examples).
FORGE_FIT_JWKS_URL = "https://forge.cdn.prod.atlassian-dev.net/.well-known/jwks.json"
FORGE_FIT_ISSUER = "forge/invocation-token"

_jwks_cache: dict | None = None
_jwks_cache_time: float = 0
_JWKS_CACHE_TTL = 3600
_JWKS_MAX_STALE_SECONDS = 24 * 3600
_JWKS_FETCH_ATTEMPTS = 3
_JWKS_FETCH_BACKOFF_SECONDS = 0.5


def validate_request(event: dict) -> str | None:
    """Return None if the request is authorized, or an error message string.

    API key auth is enforced by API Gateway — this function only
    handles Forge JWT when that mode is active.
    """
    if AUTH_MODE in ("none", "api-key"):
        return None

    if AUTH_MODE in ("forge-jwt", "both"):
        return _validate_forge_jwt(event)

    return None


def _validate_forge_jwt(event: dict) -> str | None:
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}

    # For Forge Remote, validate the Forge Invocation Token (FIT)
    # sent in Authorization Bearer header.
    auth_header = headers.get("authorization", "")
    token = auth_header.removeprefix("Bearer ").strip()
    # Compatibility fallback only if Authorization is absent.
    if not token:
        token = headers.get("x-forge-oauth-system", "").strip()
    if not token:
        return "Missing authentication token"

    try:
        jwks = _get_forge_jwks()
        kid = jwt.get_unverified_header(token).get("kid")

        rsa_key = None
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                rsa_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
                break

        if not rsa_key:
            logger.warning("JWT kid=%s not found in Forge JWKS", kid)
            return "Invalid token signing key"

        decode_opts = {"verify_exp": True, "verify_aud": bool(FORGE_APP_ID)}
        kwargs: dict = {}
        if FORGE_APP_ID:
            kwargs["audience"] = FORGE_APP_ID
        kwargs["issuer"] = FORGE_FIT_ISSUER

        jwt.decode(token, rsa_key, algorithms=["RS256"], options=decode_opts, **kwargs)
        return None

    except jwt.ExpiredSignatureError:
        return "Token expired"
    except jwt.InvalidTokenError:
        logger.warning("JWT validation failed", exc_info=True)
        return "Invalid authentication token"
    except Exception:
        logger.exception("Unexpected auth error")
        return "Authentication error"


def _get_forge_jwks() -> dict:
    global _jwks_cache, _jwks_cache_time

    now = time.time()
    if _jwks_cache and (now - _jwks_cache_time) < _JWKS_CACHE_TTL:
        return _jwks_cache

    last_error: Exception | None = None
    for attempt in range(1, _JWKS_FETCH_ATTEMPTS + 1):
        try:
            logger.info(
                "Fetching Forge FIT JWKS from %s (attempt %d/%d)",
                FORGE_FIT_JWKS_URL,
                attempt,
                _JWKS_FETCH_ATTEMPTS,
            )
            req = urllib.request.Request(FORGE_FIT_JWKS_URL, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                _jwks_cache = json.loads(resp.read())
            _jwks_cache_time = now
            return _jwks_cache
        except (URLError, HTTPError, OSError) as e:
            last_error = e
            if attempt < _JWKS_FETCH_ATTEMPTS:
                time.sleep(_JWKS_FETCH_BACKOFF_SECONDS * attempt)
            continue

    # Use stale keys as a resilience fallback for transient network/DNS failures.
    if _jwks_cache and (now - _jwks_cache_time) < _JWKS_MAX_STALE_SECONDS:
        logger.warning(
            "Using stale Forge JWKS cache due to fetch failure: %s",
            last_error,
        )
        return _jwks_cache

    raise RuntimeError(f"Failed to fetch Forge JWKS: {last_error}")
