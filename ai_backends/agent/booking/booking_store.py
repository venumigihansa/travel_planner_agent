from __future__ import annotations

from datetime import date, datetime, timezone
import json
import logging
import os
import threading
import uuid
from typing import Any

from hotel.hotel_search import build_rooms_from_rates, fetch_room_rates, XoteloConfigError

logger = logging.getLogger(__name__)

_store_lock = threading.Lock()
_STORE_PATH = os.getenv(
    "BOOKING_STORE_PATH",
    os.path.join(os.path.dirname(__file__), "..", "data", "bookings.json"),
)


def _load_store() -> dict[str, list[dict[str, Any]]]:
    if not os.path.exists(_STORE_PATH):
        return {}
    try:
        with open(_STORE_PATH, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict):
            return data
    except (OSError, json.JSONDecodeError):
        logger.exception("failed to load booking store")
    return {}


def _save_store(store: dict[str, list[dict[str, Any]]]) -> None:
    os.makedirs(os.path.dirname(_STORE_PATH), exist_ok=True)
    tmp_path = f"{_STORE_PATH}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as handle:
        json.dump(store, handle, ensure_ascii=True, indent=2)
    os.replace(tmp_path, _STORE_PATH)


_bookings_by_user: dict[str, list[dict[str, Any]]] = _load_store()


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
        _save_store(_bookings_by_user)

    return {
        "bookingId": booking_id,
        "confirmationNumber": confirmation_number,
        "message": "Booking confirmed successfully",
        "bookingDetails": new_booking,
    }


def get_bookings(user_id: str) -> list[dict[str, Any]]:
    with _store_lock:
        return [dict(b) for b in _bookings_by_user.get(user_id, [])]


def record_booking_summary(user_id: str, summary: dict[str, Any]) -> dict[str, Any] | None:
    booking_id = summary.get("bookingId") or _generate_booking_id()
    confirmation_number = summary.get("confirmationNumber") or _generate_confirmation_number()
    new_booking = {
        "bookingId": booking_id,
        "hotelId": summary.get("hotelId"),
        "hotelName": summary.get("hotelName"),
        "rooms": summary.get("rooms"),
        "roomType": summary.get("roomType"),
        "provider": summary.get("provider"),
        "userId": user_id,
        "checkInDate": summary.get("checkInDate"),
        "checkOutDate": summary.get("checkOutDate"),
        "numberOfGuests": summary.get("numberOfGuests"),
        "numberOfRooms": summary.get("numberOfRooms"),
        "pricing": summary.get("pricing") or [],
        "bookingStatus": summary.get("bookingStatus") or "CONFIRMED",
        "bookingDate": summary.get("bookingDate") or _get_current_timestamp(),
        "confirmationNumber": confirmation_number,
        "specialRequests": summary.get("specialRequests"),
    }

    with _store_lock:
        bookings = _bookings_by_user.setdefault(user_id, [])
        for booking in bookings:
            if booking.get("bookingId") == booking_id:
                return dict(booking)
        bookings.insert(0, new_booking)
        _save_store(_bookings_by_user)
    return dict(new_booking)


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
                _save_store(_bookings_by_user)
                return dict(booking)
    return None
