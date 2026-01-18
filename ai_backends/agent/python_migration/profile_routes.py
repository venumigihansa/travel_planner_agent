from __future__ import annotations

import logging
import os
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
import jwt
from jwt import PyJWKClient
from pydantic import BaseModel, Field
import psycopg

from config import Settings

logger = logging.getLogger(__name__)

settings = Settings.from_env()

router = APIRouter()

_jwks_client: PyJWKClient | None = None
_jwks_url: str | None = None


class UserUpsertRequest(BaseModel):
    userId: str = Field(..., description="Clerk user ID.")
    username: str | None = Field(None, description="Optional display name.")


class UserProfileResponse(BaseModel):
    userId: str
    username: str | None
    interests: list[str]


class InterestsUpdateRequest(BaseModel):
    interests: list[str] = Field(default_factory=list)


def _get_jwks_client() -> PyJWKClient:
    jwks_url = os.getenv("CLERK_JWKS_URL")
    if not jwks_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CLERK_JWKS_URL is not configured.",
        )
    global _jwks_client, _jwks_url
    if _jwks_client is None or _jwks_url != jwks_url:
        _jwks_client = PyJWKClient(jwks_url)
        _jwks_url = jwks_url
    return _jwks_client


def _verify_token(token: str) -> dict[str, Any]:
    jwks_client = _get_jwks_client()
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        decode_kwargs: dict[str, Any] = {
            "algorithms": ["RS256"],
            "options": {"require": ["sub", "exp", "iat"]},
        }
        issuer = os.getenv("CLERK_ISSUER")
        if issuer:
            decode_kwargs["issuer"] = issuer
        audience = os.getenv("CLERK_AUDIENCE")
        if audience:
            decode_kwargs["audience"] = audience
        return jwt.decode(token, signing_key.key, **decode_kwargs)
    except Exception as exc:
        logger.warning("JWT verification failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        ) from exc


def _get_authenticated_user_id(request: Request) -> str:
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
    payload = _verify_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject.",
        )
    return user_id


def _get_connection():
    return psycopg.connect(
        host=settings.pg_host,
        port=settings.pg_port,
        dbname=settings.pg_database,
        user=settings.pg_user,
        password=settings.pg_password or None,
    )


def _normalize_interests(values: list[str]) -> list[str]:
    seen: set[str] = set()
    cleaned: list[str] = []
    for value in values:
        if value is None:
            continue
        trimmed = value.strip()
        if not trimmed:
            continue
        key = trimmed.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(trimmed)
    return cleaned


def _ensure_user_match(expected_user_id: str, token_user_id: str) -> None:
    if expected_user_id != token_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token subject does not match requested user.",
        )


@router.post("/users", response_model=UserProfileResponse)
def create_or_update_user(request_body: UserUpsertRequest, request: Request) -> UserProfileResponse:
    token_user_id = _get_authenticated_user_id(request)
    _ensure_user_match(request_body.userId, token_user_id)

    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_activities (user_id, username)
                VALUES (%s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    username = CASE
                        WHEN EXCLUDED.username IS NOT NULL THEN EXCLUDED.username
                        ELSE user_activities.username
                    END
                RETURNING user_id, username, interests
                """,
                (request_body.userId, request_body.username),
            )
            row = cur.fetchone()

    return UserProfileResponse(
        userId=row[0],
        username=row[1],
        interests=row[2] or [],
    )


@router.get("/users/{user_id}", response_model=UserProfileResponse)
def get_user_profile(user_id: str, request: Request) -> UserProfileResponse:
    token_user_id = _get_authenticated_user_id(request)
    _ensure_user_match(user_id, token_user_id)

    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id, username, interests FROM user_activities WHERE user_id = %s",
                (user_id,),
            )
            row = cur.fetchone()

    if not row:
        return UserProfileResponse(userId=user_id, username=None, interests=[])

    return UserProfileResponse(
        userId=row[0],
        username=row[1],
        interests=row[2] or [],
    )


@router.put("/users/{user_id}/interests", response_model=UserProfileResponse)
def update_user_interests(
    user_id: str,
    request_body: InterestsUpdateRequest,
    request: Request,
) -> UserProfileResponse:
    token_user_id = _get_authenticated_user_id(request)
    _ensure_user_match(user_id, token_user_id)
    interests = _normalize_interests(request_body.interests)

    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_activities (user_id, interests)
                VALUES (%s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    interests = EXCLUDED.interests
                RETURNING user_id, username, interests
                """,
                (user_id, interests),
            )
            row = cur.fetchone()

    return UserProfileResponse(
        userId=row[0],
        username=row[1],
        interests=row[2] or [],
    )
