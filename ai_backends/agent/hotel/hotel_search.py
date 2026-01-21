from __future__ import annotations

import logging
import threading
from typing import Any

import requests

logger = logging.getLogger(__name__)

XOTELO_API_HOST = "xotelo-hotel-prices.p.rapidapi.com"
XOTELO_BASE_URL = f"https://{XOTELO_API_HOST}/api"


class HotelSearchError(RuntimeError):
    pass


class XoteloConfigError(HotelSearchError):
    pass


class HotelNotFoundError(HotelSearchError):
    pass


_hotel_cache_lock = threading.Lock()
_hotel_cache: dict[str, dict[str, Any]] = {}


def _require_api_key(api_key: str | None) -> str:
    if not api_key:
        raise XoteloConfigError("XOTELO_API_KEY is not configured.")
    return api_key


def _xotelo_get(api_key: str, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    url = f"{XOTELO_BASE_URL}/{endpoint.lstrip('/')}"
    response = requests.get(
        url,
        headers={
            "x-rapidapi-host": XOTELO_API_HOST,
            "x-rapidapi-key": api_key,
        },
        params=params,
        timeout=30,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError:
        try:
            error_body = response.json()
        except Exception:
            error_body = response.text
        logger.error(
            "xotelo request failed: %s %s params=%s status=%s response=%s",
            response.request.method if response.request else "GET",
            response.url,
            params,
            response.status_code,
            error_body,
        )
        raise

    payload = response.json()
    if payload.get("error"):
        raise HotelSearchError(f"Xotelo error: {payload.get('error')}")
    return payload


def _parse_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _normalize_hotel(hotel: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(hotel)
    hotel_id = normalized.get("hotelId")
    if not hotel_id:
        for key in ("hotel_id", "id", "hotel_key", "key"):
            value = normalized.get(key)
            if value:
                hotel_id = str(value)
                break
    if hotel_id:
        normalized["hotelId"] = hotel_id
    if not normalized.get("hotelName"):
        for key in ("name", "hotel_name", "hotel"):
            value = normalized.get(key)
            if value:
                normalized["hotelName"] = value
                break
    return normalized


def _cache_hotels(hotels: list[dict[str, Any]]) -> None:
    with _hotel_cache_lock:
        for hotel in hotels:
            hotel_id = hotel.get("hotelId")
            if hotel_id:
                _hotel_cache[hotel_id] = hotel


def get_cached_hotel(hotel_id: str) -> dict[str, Any] | None:
    with _hotel_cache_lock:
        return dict(_hotel_cache.get(hotel_id)) if hotel_id in _hotel_cache else None


def _build_rooms_from_rates(
    hotel_id: str,
    rates: list[dict[str, Any]],
    guests: int,
) -> list[dict[str, Any]]:
    rooms_out: list[dict[str, Any]] = []
    for rate in rates:
        rate_code = rate.get("code") or "OTA"
        rate_name = rate.get("name") or "OTA"
        rooms_out.append(
            {
                "roomId": f"{hotel_id}_{rate_code}",
                "hotelId": hotel_id,
                "roomType": "Standard Room",
                "roomName": f"Room via {rate_name}",
                "description": f"Book through {rate_name}",
                "maxOccupancy": guests,
                "pricePerNight": _parse_float(rate.get("rate")),
                "images": [],
                "amenities": [],
                "availableCount": 1,
            }
        )
    return rooms_out


def _sort_hotels_by_price(items: list[dict[str, Any]], ascending: bool) -> list[dict[str, Any]]:
    sorted_hotels = items[:]
    n = len(sorted_hotels)
    for i in range(n - 1):
        for j in range(n - i - 1):
            left = sorted_hotels[j].get("lowestPrice", 0)
            right = sorted_hotels[j + 1].get("lowestPrice", 0)
            if (left > right and ascending) or (left < right and not ascending):
                sorted_hotels[j], sorted_hotels[j + 1] = sorted_hotels[j + 1], sorted_hotels[j]
    return sorted_hotels


def _sort_hotels_by_rating(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sorted_hotels = items[:]
    n = len(sorted_hotels)
    for i in range(n - 1):
        for j in range(n - i - 1):
            if sorted_hotels[j].get("rating", 0) < sorted_hotels[j + 1].get("rating", 0):
                sorted_hotels[j], sorted_hotels[j + 1] = sorted_hotels[j + 1], sorted_hotels[j]
    return sorted_hotels


def _paginate(items: list[dict[str, Any]], page: int, page_size: int) -> list[dict[str, Any]]:
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end]


def _apply_filters(
    items: list[dict[str, Any]],
    destination: str | None,
    min_price: float | None,
    max_price: float | None,
    min_rating: float | None,
    amenities: list[str] | None,
    sort_by: str | None,
) -> list[dict[str, Any]]:
    filtered = items[:]

    if destination:
        tokens = [t.strip().lower() for t in destination.split(",") if t.strip()]

        def _searchable_text(hotel: dict[str, Any]) -> str:
            return " ".join(
                str(value)
                for value in (
                    hotel.get("city"),
                    hotel.get("country"),
                    hotel.get("hotelName"),
                    hotel.get("name"),
                    hotel.get("place_name"),
                    hotel.get("short_place_name"),
                )
                if value
            ).lower()

        filtered = [h for h in filtered if any(token in _searchable_text(h) for token in tokens)]

    if min_price is not None or max_price is not None:
        tmp = []
        for h in filtered:
            price = h.get("lowestPrice", 0)
            if price == 0:
                tmp.append(h)
                continue
            if min_price is not None and price < min_price:
                continue
            if max_price is not None and price > max_price:
                continue
            tmp.append(h)
        filtered = tmp

    if min_rating is not None:
        filtered = [
            h
            for h in filtered
            if h.get("rating", 0) == 0 or h.get("rating", 0) >= min_rating
        ]

    if amenities:
        filtered = [
            h
            for h in filtered
            if all(
                any(a.lower() in str(ha).lower() for ha in h.get("amenities", []))
                for a in amenities
            )
        ]

    if sort_by == "price_low":
        filtered = _sort_hotels_by_price(filtered, True)
    elif sort_by == "price_high":
        filtered = _sort_hotels_by_price(filtered, False)
    elif sort_by == "rating":
        filtered = _sort_hotels_by_rating(filtered)

    return filtered


def search_hotels(
    api_key: str | None,
    destination: str | None = None,
    check_in_date: str | None = None,
    check_out_date: str | None = None,
    guests: int = 2,
    rooms: int = 1,
    min_price: float | None = None,
    max_price: float | None = None,
    min_rating: float | None = None,
    amenities: list[str] | None = None,
    sort_by: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    if not destination:
        return {
            "hotels": [],
            "metadata": {
                "totalResults": 0,
                "page": page,
                "pageSize": page_size,
                "dataSource": "xotelo",
            },
        }

    api_key = _require_api_key(api_key)
    hotels = _xotelo_get(api_key, "search", {"query": destination}).get("result", {}).get(
        "list", []
    )
    hotels = hotels[: max(page * page_size, 30)]
    normalized = [_normalize_hotel(hotel) for hotel in hotels]
    _cache_hotels(normalized)

    filtered = _apply_filters(normalized, destination, min_price, max_price, min_rating, amenities, sort_by)
    paginated = _paginate(filtered, page, page_size)

    return {
        "hotels": paginated,
        "metadata": {
            "totalResults": len(filtered),
            "page": page,
            "pageSize": page_size,
            "dataSource": "xotelo",
        },
    }


def get_hotel_details(
    api_key: str | None,
    hotel_id: str,
    check_in_date: str | None = None,
    check_out_date: str | None = None,
    guests: int = 2,
) -> dict[str, Any]:
    cached = get_cached_hotel(hotel_id)
    if check_in_date and check_out_date:
        api_key = _require_api_key(api_key)
        rates_payload = _xotelo_get(
            api_key,
            "rates",
            params={
                "hotel_key": hotel_id,
                "chk_in": check_in_date,
                "chk_out": check_out_date,
                "adults": guests,
                "rooms": 1,
            },
        )
        rates = (rates_payload.get("result") or {}).get("rates") or []
        rooms_out = _build_rooms_from_rates(hotel_id, rates, guests)
        hotel = cached or {
            "hotelId": hotel_id,
            "hotelName": "Unknown Hotel",
            "description": "",
            "city": "",
            "country": "",
        }
        return {
            "hotel": hotel,
            "rooms": rooms_out,
            "recentReviews": [],
            "nearbyAttractions": [],
        }

    if cached:
        return {
            "hotel": cached,
            "rooms": [],
            "recentReviews": [],
            "nearbyAttractions": [],
        }

    raise HotelNotFoundError("Hotel not found.")


def check_availability(
    api_key: str | None,
    hotel_id: str,
    check_in_date: str,
    check_out_date: str,
    guests: int = 2,
    room_count: int = 1,
) -> dict[str, Any]:
    api_key = _require_api_key(api_key)
    rates_payload = _xotelo_get(
        api_key,
        "rates",
        params={
            "hotel_key": hotel_id,
            "chk_in": check_in_date,
            "chk_out": check_out_date,
            "adults": guests,
            "rooms": room_count,
        },
    )
    rates = (rates_payload.get("result") or {}).get("rates") or []
    rooms_out = _build_rooms_from_rates(hotel_id, rates, guests)
    return {
        "hotelId": hotel_id,
        "checkInDate": check_in_date,
        "checkOutDate": check_out_date,
        "availableRooms": rooms_out,
        "totalAvailable": len(rooms_out),
    }


def fetch_room_rates(
    api_key: str | None,
    hotel_id: str,
    check_in_date: str | None,
    check_out_date: str | None,
    guests: int | None,
    room_count: int | None,
) -> list[dict[str, Any]]:
    if not hotel_id or not check_in_date or not check_out_date:
        return []
    api_key = _require_api_key(api_key)
    rates_payload = _xotelo_get(
        api_key,
        "rates",
        params={
            "hotel_key": hotel_id,
            "chk_in": check_in_date,
            "chk_out": check_out_date,
            "adults": guests or 1,
            "rooms": room_count or 1,
        },
    )
    return (rates_payload.get("result") or {}).get("rates") or []


def build_rooms_from_rates(
    hotel_id: str,
    rates: list[dict[str, Any]],
    guests: int,
) -> list[dict[str, Any]]:
    return _build_rooms_from_rates(hotel_id, rates, guests)
