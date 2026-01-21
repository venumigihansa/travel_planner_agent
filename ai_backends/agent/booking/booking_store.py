from __future__ import annotations

from datetime import date, datetime, timezone
import logging
import threading
import uuid
from typing import Any

from hotel.hotel_search import build_rooms_from_rates, fetch_room_rates, XoteloConfigError

logger = logging.getLogger(__name__)

_store_lock = threading.Lock()
_bookings_by_user: dict[str, list[dict[str, Any]]] = {}


def _get_current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _generate_booking_id() -> str:
    return f"BK{uuid.uuid4().hex[:8].upper()}"


def _generate_confirmation_number() -> str:
    return f"CONF{uuid.uuid4()}"


def _calculate_nights(check_in: str | None, check_out: str | None) -> int:
    if not check_in or not check_out:
        return 0
    try:
        start = date.fromisoformat(check_in)
        end = date.fromisoformat(check_out)
        return max((end - start).days, 0)
    except Exception:
        return 0


def _build_pricing(payload: dict[str, Any], api_key: str | None) -> list[dict[str, Any]]:
    nights = _calculate_nights(payload.get("checkInDate"), payload.get("checkOutDate"))
    if nights <= 0:
        return []

    requested_rooms = payload.get("rooms") or []
    if not requested_rooms:
        return []

    try:
        rates = fetch_room_rates(
            api_key,
            payload.get("hotelId"),
            payload.get("checkInDate"),
            payload.get("checkOutDate"),
            payload.get("numberOfGuests"),
            payload.get("numberOfRooms"),
        )
    except XoteloConfigError:
        logger.warning("pricing lookup skipped: Xotelo API key missing")
        return []
    except Exception:
        logger.exception("pricing lookup failed")
        return []

    rooms = build_rooms_from_rates(
        payload.get("hotelId"),
        rates,
        payload.get("numberOfGuests") or 1,
    )
    rate_map = {
        room.get("roomId"): room.get("pricePerNight")
        for room in rooms
        if room.get("roomId")
    }

    total_per_night = 0.0
    for room in requested_rooms:
        room_id = room.get("roomId")
        count = room.get("numberOfRooms") or 1
        rate = rate_map.get(room_id)
        if rate is None:
            continue
        try:
            total_per_night += float(rate) * int(count)
        except (TypeError, ValueError):
            continue

    if total_per_night <= 0:
        return []

    total_amount = round(total_per_night * nights, 2)
    return [
        {
            "roomRate": round(total_per_night, 2),
            "totalAmount": total_amount,
            "nights": nights,
            "currency": "USD",
        }
    ]


def create_booking(payload: dict[str, Any], user_id: str, api_key: str | None) -> dict[str, Any]:
    pricing = _build_pricing(payload, api_key)
    booking_id = _generate_booking_id()
    confirmation_number = _generate_confirmation_number()

    new_booking = {
        "bookingId": booking_id,
        "hotelId": payload.get("hotelId"),
        "hotelName": payload.get("hotelName"),
        "rooms": payload.get("rooms"),
        "userId": user_id,
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

    with _store_lock:
        _bookings_by_user.setdefault(user_id, []).insert(0, new_booking)

    return {
        "bookingId": booking_id,
        "confirmationNumber": confirmation_number,
        "message": "Booking confirmed successfully",
        "bookingDetails": new_booking,
    }


def get_bookings(user_id: str) -> list[dict[str, Any]]:
    with _store_lock:
        return [dict(b) for b in _bookings_by_user.get(user_id, [])]


def get_booking(user_id: str, booking_id: str) -> dict[str, Any] | None:
    with _store_lock:
        for booking in _bookings_by_user.get(user_id, []):
            if booking.get("bookingId") == booking_id:
                return dict(booking)
    return None


def cancel_booking(user_id: str, booking_id: str) -> dict[str, Any] | None:
    with _store_lock:
        bookings = _bookings_by_user.get(user_id, [])
        for booking in bookings:
            if booking.get("bookingId") == booking_id:
                booking["bookingStatus"] = "CANCELLED"
                booking["cancellationDate"] = _get_current_timestamp()
                return dict(booking)
    return None
