from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query, Response, status

from config import Settings
from hotel.hotel_search import (
    HotelNotFoundError,
    HotelSearchError,
    XoteloConfigError,
    check_availability,
    get_hotel_details,
    search_hotels,
)

logger = logging.getLogger(__name__)

settings = Settings.from_env()

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/healthcheck")
def healthcheck() -> bool:
    return True


@router.get("/hotels/search")
def search_hotels_route(
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
    try:
        return search_hotels(
            settings.xotelo_api_key,
            destination=destination,
            check_in_date=checkInDate,
            check_out_date=checkOutDate,
            guests=guests,
            rooms=rooms,
            min_price=minPrice,
            max_price=maxPrice,
            min_rating=minRating,
            amenities=amenities,
            sort_by=sortBy,
            page=page,
            page_size=pageSize,
        )
    except XoteloConfigError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except HotelSearchError as exc:
        logger.exception("hotel search failed")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.get("/hotels/{hotel_id}")
def get_hotel_details_route(
    hotel_id: str,
    checkInDate: str | None = None,
    checkOutDate: str | None = None,
    guests: int = 2,
):
    try:
        return get_hotel_details(
            settings.xotelo_api_key,
            hotel_id=hotel_id,
            check_in_date=checkInDate,
            check_out_date=checkOutDate,
            guests=guests,
        )
    except HotelNotFoundError:
        return Response(status_code=404)
    except XoteloConfigError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except HotelSearchError as exc:
        logger.exception("hotel details lookup failed")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.get("/hotels/{hotel_id}/availability")
def check_availability_route(
    hotel_id: str,
    checkInDate: str,
    checkOutDate: str,
    guests: int = 2,
    roomCount: int = 1,
):
    try:
        return check_availability(
            settings.xotelo_api_key,
            hotel_id=hotel_id,
            check_in_date=checkInDate,
            check_out_date=checkOutDate,
            guests=guests,
            room_count=roomCount,
        )
    except XoteloConfigError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except HotelSearchError as exc:
        logger.exception("availability lookup failed")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
