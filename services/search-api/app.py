from __future__ import annotations

import importlib.util
import logging
import os
from pathlib import Path
from typing import Any

import requests
from fastapi import FastAPI, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

load_dotenv()

XOTELO_API_KEY = os.getenv("XOTELO_API_KEY")
XOTELO_API_HOST = "xotelo-hotel-prices.p.rapidapi.com"
XOTELO_BASE_URL = f"https://{XOTELO_API_HOST}/api"

_mock_module: Any | None = None

app = FastAPI(title="Xotelo Hotel Search API")

# =========================
# CORS (cloud-safe)
# =========================
cors_origins = [
    o.strip()
    for o in (os.getenv("CORS_ALLOW_ORIGINS") or "*").split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if cors_origins == ["*"] else cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _load_mock_module() -> Any:
    global _mock_module
    if _mock_module is not None:
        return _mock_module

    data_path = Path(__file__).resolve().parent / "data_mappings.py"
    spec = importlib.util.spec_from_file_location("mock_data_mappings", data_path)
    if not spec or not spec.loader:
        raise RuntimeError("Unable to load mock data mappings")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _mock_module = module
    return module


def _load_mock_data() -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    module = _load_mock_module()
    return (
        list(getattr(module, "hotels", [])),
        list(getattr(module, "rooms", [])),
        list(getattr(module, "reviews", [])),
        list(getattr(module, "nearby_attractions", [])),
    )


def _xotelo_enabled() -> bool:
    return bool(XOTELO_API_KEY)


def _xotelo_get(endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    url = f"{XOTELO_BASE_URL}/{endpoint.lstrip('/')}"
    response = requests.get(
        url,
        headers={
            "x-rapidapi-host": XOTELO_API_HOST,
            "x-rapidapi-key": XOTELO_API_KEY or "",
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
        raise ValueError(f"Xotelo error: {payload.get('error')}")
    return payload


def _parse_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


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


def _find_hotel(hotel_id: str, hotels: list[dict[str, Any]]) -> dict[str, Any] | None:
    for hotel in hotels:
        if hotel.get("hotelId") == hotel_id:
            return hotel
    return None


def _get_available_rooms(hotel_id: str, rooms: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        room
        for room in rooms
        if room.get("hotelId") == hotel_id and room.get("availableCount", 0) > 0
    ]


def _get_hotel_reviews(hotel_id: str, reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [review for review in reviews if review.get("hotelId") == hotel_id]


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
        filtered = [h for h in filtered if h.get("rating", 0) == 0 or h.get("rating", 0) >= min_rating]

    if amenities:
        filtered = [
            h for h in filtered
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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/healthcheck")
def healthcheck() -> bool:
    return True


@app.get("/hotels/search")
def search_hotels(
    destination: str | None = None,
    checkInDate: str | None = None,
    checkOutDate: str | None = None,
    guests: int = 2,
    rooms: int = Query(1),
    minPrice: float | None = None,
    maxPrice: float | None = None,
    minRating: float | None = None,
    amenities: list[str] | None = Query(None),
    sortBy: str | None = None,
    page: int = 1,
    pageSize: int = 10,
):
    used_xotelo = False

    if _xotelo_enabled() and destination:
        try:
            hotels = _xotelo_get("search", {"query": destination}).get("result", {}).get("list", [])
            hotels = hotels[: max(page * pageSize, 30)]
            used_xotelo = True
        except Exception:
            logger.exception("Xotelo failed, using mock")

    if not used_xotelo:
        hotels, _, _, _ = _load_mock_data()

    filtered = _apply_filters(hotels, destination, minPrice, maxPrice, minRating, amenities, sortBy)
    paginated = _paginate(filtered, page, pageSize)

    return {
        "hotels": paginated,
        "metadata": {
            "totalResults": len(filtered),
            "page": page,
            "pageSize": pageSize,
            "dataSource": "xotelo" if used_xotelo else "mock",
        },
    }


@app.get("/hotels/{hotel_id}")
def get_hotel_details(
    hotel_id: str,
    checkInDate: str | None = None,
    checkOutDate: str | None = None,
    guests: int = 2,
):
    if _xotelo_enabled() and checkInDate and checkOutDate:
        try:
            rates_payload = _xotelo_get(
                "rates",
                params={
                    "hotel_key": hotel_id,
                    "chk_in": checkInDate,
                    "chk_out": checkOutDate,
                    "adults": guests,
                    "rooms": 1,
                },
            )
            rates = (rates_payload.get("result") or {}).get("rates") or []
            rooms_out = _build_rooms_from_rates(hotel_id, rates, guests)
            logger.info("get_hotel_details: using xotelo data")
            return {
                "hotel": {
                    "hotelId": hotel_id,
                    "hotelName": "Unknown Hotel",
                    "description": "",
                    "city": "",
                    "country": "",
                },
                "rooms": rooms_out,
                "recentReviews": [],
                "nearbyAttractions": [],
            }
        except Exception:
            logger.exception("get_hotel_details: xotelo failed, falling back")

    hotels, rooms, reviews, nearby_attractions = _load_mock_data()
    hotel = _find_hotel(hotel_id, hotels)
    if not hotel:
        return Response(status_code=404)

    hotel_rooms = _get_available_rooms(hotel_id, rooms)
    hotel_reviews = _get_hotel_reviews(hotel_id, reviews)

    logger.info("get_hotel_details: using mock data")
    return {
        "hotel": hotel,
        "rooms": hotel_rooms,
        "recentReviews": hotel_reviews,
        "nearbyAttractions": nearby_attractions,
    }


@app.get("/hotels/{hotel_id}/availability")
def check_availability(
    hotel_id: str,
    checkInDate: str,
    checkOutDate: str,
    guests: int = 2,
    roomCount: int = 1,
):
    if _xotelo_enabled():
        try:
            rates_payload = _xotelo_get(
                "rates",
                params={
                    "hotel_key": hotel_id,
                    "chk_in": checkInDate,
                    "chk_out": checkOutDate,
                    "adults": guests,
                    "rooms": roomCount,
                },
            )
            rates = (rates_payload.get("result") or {}).get("rates") or []
            rooms_out = _build_rooms_from_rates(hotel_id, rates, guests)
            logger.info("check_availability: using xotelo data")
            return {
                "hotelId": hotel_id,
                "checkInDate": checkInDate,
                "checkOutDate": checkOutDate,
                "availableRooms": rooms_out,
                "totalAvailable": len(rooms_out),
            }
        except Exception:
            logger.exception("check_availability: xotelo failed, falling back")

    hotels, rooms, _, _ = _load_mock_data()
    if not _find_hotel(hotel_id, hotels):
        return Response(status_code=404)

    available_rooms = _get_available_rooms(hotel_id, rooms)
    logger.info("check_availability: using mock data")
    return {
        "hotelId": hotel_id,
        "checkInDate": checkInDate,
        "checkOutDate": checkOutDate,
        "availableRooms": available_rooms,
        "totalAvailable": len(available_rooms),
    }
