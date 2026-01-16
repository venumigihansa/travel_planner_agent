from __future__ import annotations

import base64
import json
import uuid
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from data_mappings import bookings as _bookings
from data_mappings import hotels as _hotels
from data_mappings import reviews as _reviews
from data_mappings import rooms as _rooms


hotels: list[dict[str, Any]] = list(_hotels)
rooms: list[dict[str, Any]] = list(_rooms)
reviews: list[dict[str, Any]] = list(_reviews)
bookings: list[dict[str, Any]] = list(_bookings)
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


def _find_hotel(hotel_id: str) -> dict[str, Any] | None:
    for hotel in hotels:
        if hotel.get("hotelId") == hotel_id:
            return hotel
    return None


def _find_room(room_id: str) -> dict[str, Any] | None:
    for room in rooms:
        if room.get("roomId") == room_id:
            return room
    return None


def _get_available_rooms(hotel_id: str) -> list[dict[str, Any]]:
    return [
        room
        for room in rooms
        if room.get("hotelId") == hotel_id and room.get("availableCount", 0) > 0
    ]


def _calculate_booking_pricing(
    room_rate: float, check_in_date: str, check_out_date: str, number_of_rooms: int
) -> dict[str, Any]:
    number_of_nights = 3
    subtotal = room_rate * number_of_nights * number_of_rooms
    taxes = subtotal * 0.12
    service_fees = subtotal * 0.05
    total_amount = subtotal + taxes + service_fees
    return {
        "roomRate": room_rate,
        "numberOfNights": number_of_nights,
        "subtotal": subtotal,
        "taxes": taxes,
        "serviceFees": service_fees,
        "totalAmount": total_amount,
        "currency": "USD",
    }


def _generate_booking_id() -> str:
    return f"BK{str(len(bookings) + 1).zfill(6)}"


def _generate_confirmation_number() -> str:
    return f"CONF{uuid.uuid4()}"


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
    hotel = _find_hotel(payload.get("hotelId", ""))
    if not hotel:
        return _error_response("Hotel not found", "HOTEL_NOT_FOUND")

    pricing: list[dict[str, Any]] = []
    for room_request in payload.get("rooms", []):
        room = _find_room(room_request.get("roomId", ""))
        if not room:
            return _error_response("Room not found", "ROOM_NOT_FOUND")
        requested_count = room_request.get("numberOfRooms", 0)
        if room.get("availableCount", 0) < requested_count:
            return _error_response("Room not available for the requested dates", "ROOM_NOT_AVAILABLE")

        pricing.append(
            _calculate_booking_pricing(
                room.get("pricePerNight", 0),
                payload.get("checkInDate", ""),
                payload.get("checkOutDate", ""),
                payload.get("numberOfRooms", 0),
            )
        )

    booking_id = _generate_booking_id()
    confirmation_number = _generate_confirmation_number()

    new_booking = {
        "bookingId": booking_id,
        "hotelId": payload.get("hotelId"),
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

    bookings.append(new_booking)

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
    return [booking for booking in bookings if booking.get("userId") == user_id]


@app.get("/bookings/{booking_id}")
def get_booking(booking_id: str, request: Request):
    error, context = _extract_auth_context(request)
    if error:
        return error

    user_id = context["userId"]
    for booking in bookings:
        if booking.get("bookingId") == booking_id:
            if booking.get("userId") != user_id:
                return _error_response("Unauthorized access to booking", "UNAUTHORIZED")
            return booking

    return _error_response("Booking not found", "BOOKING_NOT_FOUND")
