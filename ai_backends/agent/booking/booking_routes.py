from __future__ import annotations

import base64
import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Request

from booking.booking_store import cancel_booking, create_booking, get_booking, get_bookings
from config import Settings

logger = logging.getLogger(__name__)

settings = Settings.from_env()

router = APIRouter()

users: list[dict[str, Any]] = []


def _error_response(message: str, code: str) -> dict[str, Any]:
    return {
        "message": message,
        "errorCode": code,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _decode_jwt_payload(token: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) < 2:
        raise ValueError("Invalid JWT format")
    payload = parts[1]
    padding = "=" * (-len(payload) % 4)
    decoded = base64.urlsafe_b64decode(payload + padding)
    return json.loads(decoded)


def _determine_user_type(claims: dict[str, Any]) -> str:
    roles = claims.get("roles") or []
    for role in roles if isinstance(roles, list) else []:
        if "premium" in role.lower() or "vip" in role.lower():
            return "PREMIUM"

    groups = claims.get("groups") or []
    for group in groups if isinstance(groups, list) else []:
        if "premium" in group.lower() or "vip" in group.lower():
            return "PREMIUM"

    return "GUEST"


def _create_user_from_claims(claims: dict[str, Any]) -> dict[str, Any]:
    return {
        "userId": claims.get("sub"),
        "email": claims.get("email"),
        "firstName": claims.get("given_name"),
        "lastName": claims.get("family_name"),
        "phoneNumber": claims.get("phone_number"),
        "profilePicture": claims.get("picture"),
        "registrationDate": datetime.now(timezone.utc).isoformat(),
        "userType": _determine_user_type(claims),
        "authClaims": claims,
    }


def _find_or_create_user(user_id: str, claims: dict[str, Any]) -> dict[str, Any]:
    for user in users:
        if user.get("userId") == user_id:
            return {
                "userId": user.get("userId"),
                "email": claims.get("email"),
                "firstName": claims.get("given_name"),
                "lastName": claims.get("family_name"),
                "phoneNumber": claims.get("phone_number"),
                "profilePicture": claims.get("picture"),
                "registrationDate": user.get("registrationDate"),
                "userType": _determine_user_type(claims),
                "authClaims": claims,
            }

    new_user = _create_user_from_claims(claims)
    users.append(new_user)
    return new_user


def _extract_auth_context(request: Request) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    assertion = request.headers.get("x-jwt-assertion")
    if not assertion:
        return _error_response("Authentication required", "AUTH_REQUIRED"), None
    try:
        payload = _decode_jwt_payload(assertion)
    except Exception:
        return _error_response("Authentication required", "AUTH_REQUIRED"), None

    sub = payload.get("sub")
    if not sub:
        return _error_response("Authentication required", "AUTH_REQUIRED"), None

    claims = {
        "sub": sub,
        "email": payload.get("email"),
        "given_name": payload.get("given_name"),
        "family_name": payload.get("family_name"),
        "preferred_username": payload.get("preferred_username"),
        "phone_number": payload.get("phone_number"),
        "picture": payload.get("picture"),
        "roles": payload.get("roles"),
        "groups": payload.get("groups"),
    }

    return None, {"userId": sub, "userClaims": claims}


@router.get("/auth/profile")
def get_profile(request: Request):
    error, context = _extract_auth_context(request)
    if error:
        return error

    user = _find_or_create_user(context["userId"], context["userClaims"])
    return user


@router.post("/bookings", status_code=201)
def create_booking_route(payload: dict[str, Any], request: Request):
    error, context = _extract_auth_context(request)
    if error:
        return error

    user_id = context["userId"]
    return create_booking(payload, user_id, settings.xotelo_api_key)


@router.get("/bookings")
def get_bookings_route(request: Request):
    error, context = _extract_auth_context(request)
    if error:
        return error

    user_id = context["userId"]
    return get_bookings(user_id)


@router.get("/bookings/{booking_id}")
def get_booking_route(booking_id: str, request: Request):
    error, context = _extract_auth_context(request)
    if error:
        return error

    user_id = context["userId"]
    booking = get_booking(user_id, booking_id)
    if not booking:
        return _error_response("Booking not found", "BOOKING_NOT_FOUND")
    return booking


@router.put("/bookings/{booking_id}/cancel")
def cancel_booking_route(booking_id: str, request: Request):
    error, context = _extract_auth_context(request)
    if error:
        return error

    user_id = context["userId"]
    booking = cancel_booking(user_id, booking_id)
    if not booking:
        return _error_response("Booking not found", "BOOKING_NOT_FOUND")
    return {"message": "Booking cancelled successfully", "bookingDetails": booking}
