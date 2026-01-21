from __future__ import annotations

import logging
from typing import Any
import json


import psycopg
import requests
from pinecone import Pinecone
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import BaseModel, Field

from config import Settings
from booking.booking_store import get_bookings
from hotel.hotel_search import (
    HotelSearchError,
    XoteloConfigError,
    check_availability,
    get_hotel_details,
    search_hotels,
)

logger = logging.getLogger(__name__)


class RoomConfiguration(BaseModel):
    roomId: str = Field(..., description="Room ID to book.")
    numberOfRooms: int = Field(..., description="Number of rooms to book for this roomId.")


class GuestDetails(BaseModel):
    firstName: str = Field(..., description="Primary guest first name.")
    lastName: str = Field(..., description="Primary guest last name.")
    email: str = Field(..., description="Primary guest email address.")
    phoneNumber: str = Field(..., description="Primary guest phone number.")
    nationality: str | None = Field(None, description="Primary guest nationality, if available.")


class SpecialRequests(BaseModel):
    dietaryRequirements: str | None = Field(None, description="Dietary requirements, if any.")
    accessibilityNeeds: str | None = Field(None, description="Accessibility needs, if any.")
    bedPreference: str | None = Field(None, description="Bed preference, if any.")
    petFriendly: bool | None = Field(None, description="Whether the booking should be pet friendly.")
    otherRequests: str | None = Field(None, description="Other special requests.")


class BookingRequest(BaseModel):
    userId: str = Field(..., description="User ID for the booking.")
    hotelId: str = Field(..., description="Hotel ID to book.")
    hotelName: str | None = Field(None, description="Hotel name, if available.")
    rooms: list[RoomConfiguration] = Field(..., description="Room configuration(s) to book.")
    checkInDate: str = Field(..., description="Check-in date in YYYY-MM-DD format.")
    checkOutDate: str = Field(..., description="Check-out date in YYYY-MM-DD format.")
    numberOfGuests: int = Field(..., description="Total number of guests.")
    numberOfRooms: int = Field(..., description="Total number of rooms.")
    primaryGuest: GuestDetails = Field(..., description="Primary guest contact details.")
    specialRequests: SpecialRequests | None = Field(
        None, description="Optional special requests."
    )


def _pinecone_index(settings: Settings): #pineconece client initialization
    pc = Pinecone(api_key=settings.pinecone_api_key)
    return pc.Index(settings.pinecone_index_name, host=settings.pinecone_service_url)


def _embedder(settings: Settings) -> OpenAIEmbeddings: #embedding client intialization
    return OpenAIEmbeddings(
        model=settings.openai_embedding_model,
        api_key=settings.openai_api_key,
    )


def _policy_llm(settings: Settings) -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0.2,
    )


def build_tools(settings: Settings):
    def _resolve_hotel_id(hotel_id: str | None, hotel_name: str | None) -> str | None:
        candidate_name = hotel_name or hotel_id
        if hotel_id and hotel_id.strip() and " " not in hotel_id:
            return hotel_id
        if not candidate_name:
            return None
        logger.info("Resolving hotel id from name: %s", candidate_name)
        try:
            payload = search_hotels(
                settings.xotelo_api_key,
                destination=candidate_name,
                page=1,
                page_size=10,
            )
        except (HotelSearchError, XoteloConfigError):
            logger.exception("Failed to resolve hotel id from name")
            return None
        hotels = (payload or {}).get("hotels", [])
        match = next(
            (
                hotel
                for hotel in hotels
                if candidate_name.lower() in str(hotel.get("hotelName", "")).lower()
            ),
            None,
        )
        return match.get("hotelId") if match else None

    @tool
    def get_user_profile_tool(user_id: str | None = None, include_bookings: bool = True) -> str:
        """Fetch personalization profile (and optionally bookings) from Postgres."""
        user_id = user_id or settings.user_id
        logger.info("get_user_profile_tool called: user_id=%s", user_id)
        try:
            with psycopg.connect(
                host=settings.pg_host,
                port=settings.pg_port,
                dbname=settings.pg_database,
                user=settings.pg_user,
                password=settings.pg_password or None,
            ) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT username, interests FROM user_activities WHERE user_id = %s",
                        (user_id,),
                    )
                    row = cur.fetchone()
                    bookings = []
                    if include_bookings:
                        bookings = get_bookings(user_id)
            if row:
                username, interests = row
                logger.info("get_user_profile_tool found personalization data.")
                if include_bookings:
                    return json.dumps(
                        {"username": username, "interests": interests or [], "bookings": bookings},
                        ensure_ascii=True,
                    )
                return json.dumps(
                    {"username": username, "interests": interests or []},
                    ensure_ascii=True,
                )
            logger.info("get_user_profile_tool found no personalization data.")
            if include_bookings:
                return json.dumps(
                    {"username": None, "interests": [], "bookings": bookings},
                    ensure_ascii=True,
                )
            return "No personalization found for this user."
        except Exception:
            logger.exception("get_user_profile_tool failed; continuing without personalization.")
            if include_bookings:
                bookings = get_bookings(user_id)
                return json.dumps(
                    {"username": None, "interests": [], "bookings": bookings},
                    ensure_ascii=True,
                )
            return "Personalization unavailable; continue without it."

    @tool
    def query_hotel_policy_tool(question: str, hotel_id: str) -> str:
        """Retrieve hotel policy details for a given hotel ID."""
        index = _pinecone_index(settings)
        embedder = _embedder(settings)
        query_vector = embedder.embed_query(question)
        response = index.query(
            vector=query_vector,
            top_k=5,
            include_metadata=True,
            filter={"hotelId": {"$eq": hotel_id}},
        )
        matches = response.get("matches", [])
        context_chunks = [m.get("metadata", {}).get("content", "") for m in matches]
        context = "\n\n".join([c for c in context_chunks if c])
        if not context:
            return "No policy information found for that hotel."

        llm = _policy_llm(settings)
        system = SystemMessage(
            content=(
                "You are a hotel policy assistant. Answer only using the provided context. "
                "If the answer is not in the context, say so."
            )
        )
        user = HumanMessage(content=f"Question: {question}\n\nContext:\n{context}")
        result = llm.invoke([system, user])
        return result.content

    @tool
    def search_hotels_tool(
        check_in_date: str | None = None,
        check_out_date: str | None = None,
        destination: str | None = None,
        guests: int = 1,
        max_price: float | None = None,
        min_price: float | None = None,
        min_rating: float | None = None,
        page: int = 1,
        page_size: int = 10,
        rooms: int = 1,
        sort_by: str | None = None,
    ) -> dict[str, Any]:
        """Search hotels with filtering options."""
        logger.info(
            "search_hotels_tool called: destination=%s check_in_date=%s check_out_date=%s guests=%s rooms=%s",
            destination,
            check_in_date,
            check_out_date,
            guests,
            rooms,
        )
        params: dict[str, Any] = {
            "checkInDate": check_in_date,
            "checkOutDate": check_out_date,
            "destination": destination,
            "guests": guests,
            "maxPrice": max_price,
            "minPrice": min_price,
            "minRating": min_rating,
            "page": page,
            "pageSize": page_size,
            "rooms": rooms,
            "sortBy": sort_by,
        }
        params = {k: v for k, v in params.items() if v is not None}
        try:
            return search_hotels(
                settings.xotelo_api_key,
                destination=params.get("destination"),
                check_in_date=params.get("checkInDate"),
                check_out_date=params.get("checkOutDate"),
                guests=params.get("guests", 1),
                rooms=params.get("rooms", 1),
                min_price=params.get("minPrice"),
                max_price=params.get("maxPrice"),
                min_rating=params.get("minRating"),
                amenities=params.get("amenities"),
                sort_by=params.get("sortBy"),
                page=params.get("page", 1),
                page_size=params.get("pageSize", 10),
            )
        except XoteloConfigError as exc:
            return {"error": str(exc)}
        except HotelSearchError:
            logger.exception("search_hotels_tool failed")
            return {"error": "Hotel search failed."}

    @tool
    def get_hotel_info_tool(hotel_id: str) -> dict[str, Any]:
        """Retrieve detailed information about a hotel."""
        logger.info("get_hotel_info_tool called: hotel_id=%s", hotel_id)
        try:
            return get_hotel_details(settings.xotelo_api_key, hotel_id=hotel_id)
        except XoteloConfigError as exc:
            return {"error": str(exc)}
        except HotelSearchError:
            logger.exception("get_hotel_info_tool failed")
            return {"error": "Hotel details unavailable."}

    @tool
    def check_hotel_availability_tool(
        check_in_date: str,
        check_out_date: str,
        guests: int,
        hotel_id: str,
        room_count: int,
        hotel_name: str | None = None,
    ) -> dict[str, Any]:
        """Check availability before recommending a hotel."""
        resolved_id = _resolve_hotel_id(hotel_id, hotel_name)
        if not resolved_id:
            return {"error": "Hotel not found. Provide a valid hotel_id or hotel_name."}
        logger.info(
            "check_hotel_availability_tool called: hotel_id=%s check_in_date=%s check_out_date=%s guests=%s room_count=%s",
            resolved_id,
            check_in_date,
            check_out_date,
            guests,
            room_count,
        )
        params = {
            "checkInDate": check_in_date,
            "checkOutDate": check_out_date,
            "guests": guests,
            "roomCount": room_count,
        }
        try:
            return check_availability(
                settings.xotelo_api_key,
                hotel_id=resolved_id,
                check_in_date=params["checkInDate"],
                check_out_date=params["checkOutDate"],
                guests=params["guests"],
                room_count=params["roomCount"],
            )
        except XoteloConfigError as exc:
            return {"error": str(exc)}
        except HotelSearchError:
            logger.exception("check_hotel_availability_tool failed")
            return {"error": "Hotel availability unavailable."}

    @tool(args_schema=BookingRequest)
    def create_booking_tool(
        userId: str,
        hotelId: str,
        rooms: list[RoomConfiguration],
        checkInDate: str,
        checkOutDate: str,
        numberOfGuests: int,
        numberOfRooms: int,
        primaryGuest: GuestDetails,
        specialRequests: SpecialRequests | None = None,
        hotelName: str | None = None,
    ) -> dict[str, Any]:
        """Create a booking via the booking API."""
        logger.info(
            "create_booking_tool called: user_id=%s hotel_id=%s check_in_date=%s check_out_date=%s number_of_rooms=%s",
            userId,
            hotelId,
            checkInDate,
            checkOutDate,
            numberOfRooms,
        )
        payload = {
            "userId": userId,
            "hotelId": hotelId,
            "hotelName": hotelName,
            "rooms": [room.model_dump() for room in rooms],
            "checkInDate": checkInDate,
            "checkOutDate": checkOutDate,
            "numberOfGuests": numberOfGuests,
            "numberOfRooms": numberOfRooms,
            "primaryGuest": primaryGuest.model_dump(),
            "specialRequests": specialRequests.model_dump() if specialRequests else None,
        }
        from booking.booking_store import create_booking

        return create_booking(payload, userId, settings.xotelo_api_key)

    @tool
    def get_weather_forecast_tool(location: str, date: str | None = None) -> str:
        """Retrieve weather using WeatherAPI.com."""
        if not settings.weather_api_key:
            return "Weather service is not configured."
        logger.info("get_weather_forecast_tool called: location=%s date=%s", location, date)
        base_url = settings.weather_api_base_url.rstrip("/")
        if date:
            endpoint = f"{base_url}/forecast.json"
            params = {"key": settings.weather_api_key, "q": location, "dt": date}
        else:
            endpoint = f"{base_url}/current.json"
            params = {"key": settings.weather_api_key, "q": location}
        response = requests.get(endpoint, params=params, timeout=30)
        response.raise_for_status()
        return response.text

    return [
        get_user_profile_tool,
        query_hotel_policy_tool,
        search_hotels_tool,
        get_hotel_info_tool,
        create_booking_tool,
        check_hotel_availability_tool,
        get_weather_forecast_tool,
    ]
