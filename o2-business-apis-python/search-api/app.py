from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Query, Response
from fastapi.middleware.cors import CORSMiddleware

from data_mappings import hotels as _hotels
from data_mappings import nearby_attractions as _nearby_attractions
from data_mappings import reviews as _reviews
from data_mappings import rooms as _rooms


hotels: list[dict[str, Any]] = list(_hotels)
rooms: list[dict[str, Any]] = list(_rooms)
reviews: list[dict[str, Any]] = list(_reviews)
nearby_attractions: list[dict[str, Any]] = list(_nearby_attractions)


app = FastAPI(title="Hotel Search API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
    max_age=84900,
)


@app.get("/healthcheck")
def healthcheck() -> bool:
    return True


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


def _get_hotel_reviews(hotel_id: str) -> list[dict[str, Any]]:
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


def _search_hotels(
    destination: str | None,
    min_price: float | None,
    max_price: float | None,
    min_rating: float | None,
    amenities: list[str] | None,
    sort_by: str | None,
) -> list[dict[str, Any]]:
    filtered = hotels[:]

    if destination:
        lower_destination = destination.lower()
        filtered = [
            hotel
            for hotel in filtered
            if lower_destination in str(hotel.get("city", "")).lower()
            or lower_destination in str(hotel.get("country", "")).lower()
        ]

    if min_price is not None or max_price is not None:
        price_filtered = []
        for hotel in filtered:
            include = True
            hotel_price = hotel.get("lowestPrice", 0)
            if min_price is not None and hotel_price < min_price:
                include = False
            if max_price is not None and hotel_price > max_price:
                include = False
            if include:
                price_filtered.append(hotel)
        filtered = price_filtered

    if min_rating is not None:
        filtered = [hotel for hotel in filtered if hotel.get("rating", 0) >= min_rating]

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
    filtered = _search_hotels(destination, minPrice, maxPrice, minRating, amenities, sortBy)
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
    }

    return {"hotels": paginated, "metadata": metadata}


@app.get("/hotels/{hotel_id}/attractions")
def get_hotel_attractions(hotel_id: str) -> dict[str, Any]:
    for attraction in nearby_attractions:
        if attraction.get("hotelId") == hotel_id:
            return attraction
    return {"hotelId": hotel_id, "attractions": []}


@app.get("/hotels/{hotel_id}")
def get_hotel_details(hotel_id: str):
    hotel = _find_hotel(hotel_id)
    if not hotel:
        return Response(status_code=404)

    hotel_rooms = _get_available_rooms(hotel_id)
    hotel_reviews = _get_hotel_reviews(hotel_id)

    default_attractions = [
        {
            "name": "Central Park",
            "category": "Park",
            "distance": 0.5,
            "location": {"latitude": 0, "longitude": 0},
        },
        {
            "name": "Museum of Modern Art",
            "category": "Museum",
            "distance": 1.2,
            "location": {"latitude": 0, "longitude": 0},
        },
        {
            "name": "Times Square",
            "category": "Entertainment",
            "distance": 2.1,
            "location": {"latitude": 0, "longitude": 0},
        },
    ]

    return {
        "hotel": hotel,
        "rooms": hotel_rooms,
        "recentReviews": hotel_reviews,
        "nearbyAttractions": default_attractions,
    }


@app.get("/hotels/{hotel_id}/availability")
def check_availability(
    hotel_id: str,
    checkInDate: str,
    checkOutDate: str,
    guests: int = 2,
    roomCount: int = 1,
):
    if not _find_hotel(hotel_id):
        return Response(status_code=404)

    available_rooms = _get_available_rooms(hotel_id)
    return {
        "hotelId": hotel_id,
        "checkInDate": checkInDate,
        "checkOutDate": checkOutDate,
        "availableRooms": available_rooms,
        "totalAvailable": len(available_rooms),
    }
