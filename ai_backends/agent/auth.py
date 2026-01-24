from __future__ import annotations

import logging
import os
from typing import Any

from fastapi import HTTPException, Request, status
import jwt
from jwt import PyJWKClient

logger = logging.getLogger(__name__)

_jwks_client: PyJWKClient | None = None
_jwks_url: str | None = None


def _resolve_auth_env(name: str, fallback: str) -> str | None:
    value = os.getenv(name)
    if value:
        return value
    return os.getenv(fallback)


def _get_jwks_client() -> PyJWKClient:
    jwks_url = _resolve_auth_env("ASGARDEO_JWKS_URL", "CLERK_JWKS_URL")
    if not jwks_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ASGARDEO_JWKS_URL is not configured.",
        )
    global _jwks_client, _jwks_url
    if _jwks_client is None or _jwks_url != jwks_url:
        _jwks_client = PyJWKClient(jwks_url)
        _jwks_url = jwks_url
    return _jwks_client


def verify_token(token: str) -> dict[str, Any]:
    jwks_client = _get_jwks_client()
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        decode_kwargs: dict[str, Any] = {
            "algorithms": ["RS256"],
            "options": {"require": ["sub", "exp", "iat"]},
        }
        issuer = _resolve_auth_env("ASGARDEO_ISSUER", "CLERK_ISSUER")
        if issuer:
            decode_kwargs["issuer"] = issuer
        audience = _resolve_auth_env("ASGARDEO_AUDIENCE", "CLERK_AUDIENCE")
        if audience:
            decode_kwargs["audience"] = audience
        return jwt.decode(token, signing_key.key, **decode_kwargs)
    except Exception as exc:
        logger.warning("JWT verification failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        ) from exc


def get_authenticated_user_id(request: Request) -> str:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
        )
    token = auth_header.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
        )
    payload = verify_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject.",
        )
    return str(user_id)


def get_optional_user_id(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
        )
    token = auth_header.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
        )
    payload = verify_token(token)
    return payload.get("sub")
