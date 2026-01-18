from __future__ import annotations

import base64
import json
import logging
import os
import uuid
from typing import Any

import psycopg
from psycopg.types.json import Json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

users: list[dict[str, Any]] = []


app = FastAPI(title="Hotel Booking API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "x-jwt-assertion"],
    max_age=84900,
)


def _error_response(message: str, code: str) -> dict[str, Any]:
    return {
        "message": message,
        "errorCode": code,
        "timestamp": _get_current_timestamp(),
    }


def _get_current_timestamp() -> str:
    return "2024-01-15T10:30:00Z"


def _generate_booking_id() -> str:
    return f"BK{uuid.uuid4().hex[:8].upper()}"


def _generate_confirmation_number() -> str:
    return f"CONF{uuid.uuid4()}"


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required env var: {name}")
    return value


def _get_db_connection() -> psycopg.Connection[Any]:
    return psycopg.connect(
        host=os.getenv("PG_HOST", "localhost"),
        port=int(os.getenv("PG_PORT", "5432")),
        dbname=_require_env("PG_DATABASE"),
        user=_require_env("PG_USER"),
        password=os.getenv("PG_PASSWORD") or None,
    )


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
        "registrationDate": _get_current_timestamp(),
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


@app.get("/auth/profile")
def get_profile(request: Request):
    error, context = _extract_auth_context(request)
    if error:
        return error

    user = _find_or_create_user(context["userId"], context["userClaims"])
    return user


@app.post("/bookings", status_code=201)
def create_booking(payload: dict[str, Any]):
    pricing: list[dict[str, Any]] = []

    booking_id = _generate_booking_id()
    confirmation_number = _generate_confirmation_number()

    new_booking = {
        "bookingId": booking_id,
        "hotelId": payload.get("hotelId"),
        "hotelName": payload.get("hotelName"),
        "rooms": payload.get("rooms"),
        "userId": payload.get("userId"),
        "checkInDate": payload.get("checkInDate"),
        "checkOutDate": payload.get("checkOutDate"),
        "numberOfGuests": payload.get("numberOfGuests"),
        "primaryGuest": payload.get("primaryGuest"),
        "pricing": pricing,
        "bookingStatus": "CONFIRMED",
        "bookingDate": _get_current_timestamp(),
        "confirmationNumber": confirmation_number,
        "specialRequests": payload.get("specialRequests"),
    }

    try:
        with _get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO bookings (
                        booking_id,
                        user_id,
                        hotel_id,
                        hotel_name,
                        check_in_date,
                        check_out_date,
                        booking_status,
                        confirmation_number,
                        details
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        booking_id,
                        payload.get("userId"),
                        payload.get("hotelId"),
                        payload.get("hotelName"),
                        payload.get("checkInDate"),
                        payload.get("checkOutDate"),
                        new_booking.get("bookingStatus"),
                        confirmation_number,
                        Json(new_booking),
                    ),
                )
    except Exception:
        logger.exception("create_booking: failed to persist booking")
        return _error_response("Booking persistence failed", "BOOKING_PERSIST_FAILED")

    return {
        "bookingId": booking_id,
        "confirmationNumber": confirmation_number,
        "message": "Booking confirmed successfully",
        "bookingDetails": new_booking,
    }


@app.get("/bookings")
def get_bookings(request: Request):
    error, context = _extract_auth_context(request)
    if error:
        return error

    user_id = context["userId"]
    try:
        with _get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT details FROM bookings WHERE user_id = %s ORDER BY booking_date DESC",
                    (user_id,),
                )
                rows = cur.fetchall()
        return [row[0] for row in rows]
    except Exception:
        logger.exception("get_bookings: failed to fetch bookings")
        return _error_response("Database unavailable", "DB_UNAVAILABLE")


@app.get("/bookings/{booking_id}")
def get_booking(booking_id: str, request: Request):
    error, context = _extract_auth_context(request)
    if error:
        return error

    user_id = context["userId"]
    try:
        with _get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT details FROM bookings WHERE booking_id = %s AND user_id = %s",
                    (booking_id, user_id),
                )
                row = cur.fetchone()
        if not row:
            return _error_response("Booking not found", "BOOKING_NOT_FOUND")
        return row[0]
    except Exception:
        logger.exception("get_booking: failed to fetch booking")
        return _error_response("Database unavailable", "DB_UNAVAILABLE")
