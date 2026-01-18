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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
    max_age=84900,
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


def _load_mock_data() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
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
        error_body: Any = ""
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
        logger.error("xotelo request error: endpoint=%s params=%s error=%s", endpoint, params, payload.get("error"))
        raise ValueError(f"Xotelo error: {payload.get('error')}")
    return payload


def _parse_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


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
            should_swap = left > right if ascending else left < right
            if should_swap:
                sorted_hotels[j], sorted_hotels[j + 1] = sorted_hotels[j + 1], sorted_hotels[j]
    return sorted_hotels


def _sort_hotels_by_rating(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sorted_hotels = items[:]
    n = len(sorted_hotels)
    for i in range(n - 1):
        for j in range(n - i - 1):
            left = sorted_hotels[j].get("rating", 0)
            right = sorted_hotels[j + 1].get("rating", 0)
            if left < right:
                sorted_hotels[j], sorted_hotels[j + 1] = sorted_hotels[j + 1], sorted_hotels[j]
    return sorted_hotels


def _paginate(items: list[dict[str, Any]], page: int, page_size: int) -> list[dict[str, Any]]:
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    if start_index >= len(items):
        return []
    return items[start_index:min(end_index, len(items))]


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
        lower_destination = destination.lower()
        filtered = [
            hotel
            for hotel in filtered
            if lower_destination in str(hotel.get("city", "")).lower()
            or lower_destination in str(hotel.get("country", "")).lower()
            or lower_destination in str(hotel.get("hotelName", "")).lower()
        ]

    # Only apply price filtering if we have actual pricing data (lowestPrice > 0)
    # When dates aren't provided, lowestPrice is 0.0, so we skip price filters
    if min_price is not None or max_price is not None:
        price_filtered = []
        for hotel in filtered:
            hotel_price = hotel.get("lowestPrice", 0)
            
            # Skip price filtering for hotels without pricing data
            if hotel_price == 0:
                price_filtered.append(hotel)
                continue
                
            include = True
            if min_price is not None and hotel_price < min_price:
                include = False
            if max_price is not None and hotel_price > max_price:
                include = False
            if include:
                price_filtered.append(hotel)
        filtered = price_filtered

    # Only apply rating filtering if hotels have rating data
    # When using reference data without offers, ratings may be 0.0
    if min_rating is not None:
        rated_hotels = []
        for hotel in filtered:
            hotel_rating = hotel.get("rating", 0)
            # If rating is 0, it means no rating data - include it (don't filter by missing data)
            # Only filter out hotels that have ratings below the minimum
            if hotel_rating == 0 or hotel_rating >= min_rating:
                rated_hotels.append(hotel)
        filtered = rated_hotels

    if amenities:
        amenity_filtered = []
        for hotel in filtered:
            hotel_amenities = [str(a).lower() for a in hotel.get("amenities", [])]
            has_all = True
            for amenity in amenities:
                if not any(amenity.lower() in ha for ha in hotel_amenities):
                    has_all = False
                    break
            if has_all:
                amenity_filtered.append(hotel)
        filtered = amenity_filtered

    if sort_by == "price_low":
        filtered = _sort_hotels_by_price(filtered, True)
    elif sort_by == "price_high":
        filtered = _sort_hotels_by_price(filtered, False)
    elif sort_by == "rating":
        filtered = _sort_hotels_by_rating(filtered)

    return filtered


def _extract_city_country(place: str | None) -> tuple[str, str]:
    if not place:
        return "", ""
    parts = [part.strip() for part in place.split(",") if part.strip()]
    if not parts:
        return "", ""
    city = parts[0]
    country = parts[-1] if len(parts) > 1 else ""
    return city, country


def _normalize_xotelo_search_result(item: dict[str, Any]) -> dict[str, Any]:
    city, country = _extract_city_country(item.get("short_place_name"))
    return {
        "hotelId": item.get("hotel_key") or "",
        "hotelName": item.get("name") or "Unknown Hotel",
        "description": "",
        "city": city,
        "country": country,
        "rating": 0.0,
        "amenities": [],
        "lowestPrice": 0.0,
        "image": item.get("image"),
        "address": item.get("street_address"),
    }


def _normalize_xotelo_list_result(item: dict[str, Any]) -> dict[str, Any]:
    review_summary = item.get("review_summary") or {}
    price_ranges = item.get("price_ranges") or {}
    geo = item.get("geo") or {}
    mentions = item.get("mentions") or []
    if not isinstance(mentions, list):
        mentions = []
    return {
        "hotelId": item.get("key") or "",
        "hotelName": item.get("name") or "Unknown Hotel",
        "description": ", ".join(mentions),
        "city": "",
        "country": "",
        "rating": _parse_float(review_summary.get("rating")),
        "reviewCount": int(review_summary.get("count") or 0),
        "amenities": mentions,
        "lowestPrice": _parse_float(price_ranges.get("minimum")),
        "maxPrice": _parse_float(price_ranges.get("maximum")),
        "image": item.get("image"),
        "latitude": geo.get("latitude"),
        "longitude": geo.get("longitude"),
    }


def _search_hotels_xotelo(
    destination: str,
    check_in_date: str | None,
    check_out_date: str | None,
    guests: int,
    limit: int,
) -> list[dict[str, Any]]:
    logger.info("Searching hotels via Xotelo for '%s'", destination)
    payload = _xotelo_get("search", params={"query": destination, "location_type": "accommodation"})
    results = payload.get("result") or {}
    items = results.get("list") or []
    if not isinstance(items, list):
        items = []

    items = items[:limit]
    hotels: list[dict[str, Any]] = []
    for item in items:
        hotel = _normalize_xotelo_search_result(item)
        hotel_key = item.get("hotel_key") or hotel.get("hotelId")
        if check_in_date and check_out_date and hotel_key:
            try:
                rates_payload = _xotelo_get(
                    "rates",
                    params={
                        "hotel_key": hotel_key,
                        "chk_in": check_in_date,
                        "chk_out": check_out_date,
                        "adults": guests,
                        "rooms": 1,
                    },
                )
                rates_result = rates_payload.get("result") or {}
                rates = rates_result.get("rates") or []
                if isinstance(rates, list):
                    prices = [_parse_float(rate.get("rate")) for rate in rates]
                    if prices:
                        hotel["lowestPrice"] = min(prices)
            except Exception as exc:
                logger.warning("Failed to get rates for hotel %s: %s", hotel_key, exc)
        hotels.append(hotel)

    logger.info("Successfully retrieved %d hotels from Xotelo", len(hotels))
    return hotels


def _build_rooms_from_rates(hotel_id: str, rates: list[dict[str, Any]], guests: int) -> list[dict[str, Any]]:
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


def _fallback_search(
    destination: str | None,
    min_price: float | None,
    max_price: float | None,
    min_rating: float | None,
    amenities: list[str] | None,
    sort_by: str | None,
) -> list[dict[str, Any]]:
    hotels, _, _, _ = _load_mock_data()
    return _apply_filters(hotels, destination, min_price, max_price, min_rating, amenities, sort_by)


@app.get("/healthcheck")
def healthcheck() -> bool:
    return True


@app.get("/hotels/search")
def search_hotels(
    destination: str | None = None,
    checkInDate: str | None = None,
    checkOutDate: str | None = None,
    guests: int = 2,
    rooms_param: int = Query(1, alias="rooms"),
    minPrice: float | None = None,
    maxPrice: float | None = None,
    minRating: float | None = None,
    amenities: list[str] | None = Query(None),
    propertyTypes: list[str] | None = Query(None),
    sortBy: str | None = None,
    page: int = 1,
    pageSize: int = 10,
) -> dict[str, Any]:
    used_xotelo = False
    filtered: list[dict[str, Any]] = []

    if _xotelo_enabled() and destination:
        try:
            filtered = _search_hotels_xotelo(
                destination=destination,
                check_in_date=checkInDate,
                check_out_date=checkOutDate,
                guests=guests,
                limit=max(page * pageSize, 30),
            )
            used_xotelo = True
        except Exception as exc:
            logger.exception("search_hotels: xotelo failed, falling back: %s", exc)
    else:
        if not _xotelo_enabled():
            logger.info("search_hotels: xotelo disabled, using mock data")
        elif not destination:
            logger.info("search_hotels: no destination provided, using mock data")

    if not used_xotelo:
        filtered = _fallback_search(destination, minPrice, maxPrice, minRating, amenities, sortBy)
        logger.info("Using mock data as fallback: %d hotels before pagination", len(filtered))
    else:
        logger.info("Before filters: %d hotels", len(filtered))
        filtered = _apply_filters(filtered, destination, minPrice, maxPrice, minRating, amenities, sortBy)
        logger.info("After filters: %d hotels", len(filtered))

    paginated = _paginate(filtered, page, pageSize)
    total_pages = (len(filtered) + pageSize - 1) // pageSize

    applied_filters = {
        "destination": destination,
        "checkInDate": checkInDate,
        "checkOutDate": checkOutDate,
        "guests": guests,
        "rooms": rooms_param,
        "priceRange": None
        if minPrice is None and maxPrice is None
        else {"min": minPrice or 0.0, "max": maxPrice or 999999.0},
        "minRating": minRating,
        "amenities": amenities,
        "propertyTypes": propertyTypes,
    }

    metadata = {
        "totalResults": len(filtered),
        "currentPage": page,
        "totalPages": total_pages,
        "pageSize": pageSize,
        "appliedFilters": applied_filters,
        "dataSource": "xotelo" if used_xotelo else "mock",
    }

    return {"hotels": paginated, "metadata": metadata}


@app.get("/hotels/{hotel_id}")
def get_hotel_details(hotel_id: str, checkInDate: str | None = None, checkOutDate: str | None = None, guests: int = 2):
    if _xotelo_enabled() and checkInDate and checkOutDate:
        try:
            hotel_payload = _xotelo_get(
                "search",
                params={"query": hotel_id, "location_type": "accommodation"},
            )
            hotels_list = (hotel_payload.get("result") or {}).get("list") or []
            matching_hotel = next(
                (item for item in hotels_list if item.get("hotel_key") == hotel_id),
                None,
            )
            hotel = (
                _normalize_xotelo_search_result(matching_hotel)
                if matching_hotel
                else {"hotelId": hotel_id, "hotelName": "Unknown Hotel", "description": "", "city": "", "country": ""}
            )

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
                "hotel": hotel,
                "rooms": rooms_out,
                "recentReviews": [],
                "nearbyAttractions": [],
            }
        except Exception as exc:
            logger.exception("get_hotel_details: xotelo failed, falling back: %s", exc)

    hotels, rooms, reviews, _ = _load_mock_data()
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
        "nearbyAttractions": [],
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
        except Exception as exc:
            logger.exception("check_availability: xotelo failed, falling back: %s", exc)

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
