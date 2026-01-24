from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Request

from booking.booking_store import cancel_booking, create_booking, get_booking, get_bookings
from config import Settings
from auth import get_optional_user_id

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


def _resolve_user_id(request: Request, payload: dict[str, Any] | None = None) -> str | None:
    token_user_id = get_optional_user_id(request)
    if token_user_id:
        return str(token_user_id)
    if payload and payload.get("userId"):
        return str(payload["userId"])
    header_user = request.headers.get("x-user-id")
    if header_user:
        return header_user
    return None


@router.get("/auth/profile")
def get_profile(request: Request):
    user_id = _resolve_user_id(request)
    if not user_id:
        return _error_response("User ID required", "USER_ID_REQUIRED")
    return {
        "userId": user_id,
        "registrationDate": datetime.now(timezone.utc).isoformat(),
        "userType": "GUEST",
    }


@router.post("/bookings", status_code=201)
def create_booking_route(payload: dict[str, Any], request: Request):
    user_id = _resolve_user_id(request, payload)
    if not user_id:
        return _error_response("User ID required", "USER_ID_REQUIRED")

    return create_booking(payload, user_id, settings.xotelo_api_key)


@router.get("/bookings")
def get_bookings_route(request: Request):
    user_id = _resolve_user_id(request)
    if not user_id:
        return _error_response("User ID required", "USER_ID_REQUIRED")

    return get_bookings(user_id)


@router.get("/bookings/{booking_id}")
def get_booking_route(booking_id: str, request: Request):
    user_id = _resolve_user_id(request)
    if not user_id:
        return _error_response("User ID required", "USER_ID_REQUIRED")

    booking = get_booking(user_id, booking_id)
    if not booking:
        return _error_response("Booking not found", "BOOKING_NOT_FOUND")
    return booking


@router.put("/bookings/{booking_id}/cancel")
def cancel_booking_route(booking_id: str, request: Request):
    user_id = _resolve_user_id(request)
    if not user_id:
        return _error_response("User ID required", "USER_ID_REQUIRED")

    booking = cancel_booking(user_id, booking_id)
    if not booking:
        return _error_response("Booking not found", "BOOKING_NOT_FOUND")
    return {"message": "Booking cancelled successfully", "bookingDetails": booking}
