from __future__ import annotations

import logging
from typing import Any
import json

import requests
from pinecone import Pinecone
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import BaseModel, Field

from config import Settings
from hotel.hotel_search import (
    HotelSearchError,
    XoteloConfigError,
    check_availability,
    fetch_room_rates,
    get_hotel_details,
    search_hotels,
)
from request_context import get_current_user_id

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


def _pinecone_index(settings: Settings):
    pc = Pinecone(api_key=settings.pinecone_api_key)
    return pc.Index(settings.pinecone_index_name, host=settings.pinecone_service_url)


def _embedder(settings: Settings) -> OpenAIEmbeddings:
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
    def _require_serper_api_key() -> str:
        if not settings.serper_api_key:
            raise ValueError("SERPER_API_KEY is not configured.")
        return settings.serper_api_key

    def _serper_post(payload: dict[str, Any]) -> dict[str, Any]:
        api_key = _require_serper_api_key()
        response = requests.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def _pick_first_organic(result: dict[str, Any]) -> dict[str, Any] | None:
        organic = result.get("organic") or []
        return organic[0] if organic else None

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
    def get_user_profile_tool(user_id: str | None = None, user_name: str | None = None) -> dict[str, Any]:
        """Return basic user personalization details from environment defaults."""
        resolved_user_id = user_id or settings.user_id
        resolved_user_name = user_name or settings.user_name
        return {
            "userId": resolved_user_id,
            "username": resolved_user_name,
            "interests": [],
            "source": "env",
        }

    @tool
    def query_hotel_policy_tool(
        question: str,
        hotel_id: str | None = None,
        hotel_name: str | None = None,
    ) -> str:
        """Retrieve hotel policy details; fall back to web search if not found in Pinecone."""
        resolved_id = _resolve_hotel_id(hotel_id, hotel_name)
        if resolved_id:
            index = _pinecone_index(settings)
            embedder = _embedder(settings)
            query_vector = embedder.embed_query(question)
            response = index.query(
                vector=query_vector,
                top_k=5,
                include_metadata=True,
                filter={"hotelId": {"$eq": resolved_id}},
            )
            matches = response.get("matches", [])
            context_chunks = [m.get("metadata", {}).get("content", "") for m in matches]
            context = "\n\n".join([c for c in context_chunks if c])
            if context:
                llm = _policy_llm(settings)
                system = SystemMessage(
                    content=(
                        "You are a hotel policy assistant. Answer only using the provided context. "
                        "If the answer is not in the context, say so."
                    )
                )
                user = HumanMessage(content=f"Question: {question}\n\nContext:\n{context}")
                result = llm.invoke([system, user])
                return json.dumps(
                    {
                        "found": True,
                        "source": "pinecone",
                        "hotelId": resolved_id,
                        "answer": result.content,
                    },
                    ensure_ascii=True,
                )

            policy_result = {
                "found": False,
                "source": "pinecone",
                "hotelId": resolved_id,
                "answer": "",
            }
            if policy_result.get("found"):
                return json.dumps(policy_result, ensure_ascii=True)

        if not hotel_name and not resolved_id:
            return json.dumps(
                {
                    "found": False,
                    "source": "serper",
                    "hotelId": resolved_id,
                    "answer": "",
                    "note": "Hotel name or ID required for web search.",
                },
                ensure_ascii=True,
            )

        query_name = hotel_name or hotel_id or resolved_id or ""
        web_result = search_policy_web_tool.invoke({"hotel_name": query_name, "question": question})
        try:
            web_payload = json.loads(web_result)
        except json.JSONDecodeError:
            return json.dumps(
                {
                    "found": False,
                    "source": "serper",
                    "hotelId": resolved_id,
                    "answer": "",
                    "error": "Failed to parse web search result.",
                },
                ensure_ascii=True,
            )

        return json.dumps(
            {
                "found": bool(web_payload.get("found")),
                "source": web_payload.get("source", "serper"),
                "hotelId": resolved_id,
                "answer": web_payload.get("snippet", ""),
                "title": web_payload.get("title", ""),
                "url": web_payload.get("url", ""),
                "query": web_payload.get("query", ""),
            },
            ensure_ascii=True,
        )

    @tool
    def search_policy_web_tool(hotel_name: str, question: str) -> str:
        """Search the web for hotel policy pages (Serper)."""
        query = f"{hotel_name} {question}"
        try:
            result = _serper_post({"q": query})
        except Exception as exc:
            logger.exception("search_policy_web_tool failed")
            return json.dumps(
                {"error": str(exc), "source": "serper", "query": query},
                ensure_ascii=True,
            )
        top = _pick_first_organic(result)
        if not top:
            return json.dumps(
                {"found": False, "source": "serper", "query": query},
                ensure_ascii=True,
            )
        return json.dumps(
            {
                "found": True,
                "source": "serper",
                "query": query,
                "title": top.get("title"),
                "url": top.get("link"),
                "snippet": top.get("snippet"),
            },
            ensure_ascii=True,
        )

    @tool
    def geocode_hotel_tool(address: str) -> dict[str, Any]:
        """Resolve an address to latitude/longitude via Nominatim."""
        base_url = (settings.nominatim_base_url or "https://nominatim.openstreetmap.org").rstrip("/")
        try:
            response = requests.get(
                f"{base_url}/search",
                params={"q": address, "format": "json", "limit": 1},
                headers={"User-Agent": "travel-planner-agent/1.0"},
                timeout=30,
            )
            response.raise_for_status()
        except Exception as exc:
            logger.exception("geocode_hotel_tool failed")
            return {"error": str(exc)}
        results = response.json()
        if not results:
            return {"error": "No geocoding results found."}
        top = results[0]
        lat = top.get("lat")
        lon = top.get("lon")
        return {
            "lat": float(lat) if lat else None,
            "lon": float(lon) if lon else None,
            "map_url": f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=18/{lat}/{lon}",
            "display_name": top.get("display_name"),
        }

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
    def get_hotel_info_tool(hotel_id: str | None = None, hotel_name: str | None = None) -> dict[str, Any]:
        """Retrieve detailed information about a hotel."""
        candidate = hotel_id or hotel_name or ""
        if candidate.lower().startswith("user_"):
            return {"error": "Invalid hotel_id provided. Ask for a hotel name or destination."}
        resolved_id = _resolve_hotel_id(hotel_id, hotel_name)
        if not resolved_id:
            return {"error": "Hotel not found. Provide a valid hotel_id or hotel_name."}
        logger.info("get_hotel_info_tool called: hotel_id=%s", resolved_id)
        try:
            return get_hotel_details(settings.xotelo_api_key, hotel_id=resolved_id)
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
        candidate_name = hotel_name
        if not candidate_name and hotel_id and " " in hotel_id:
            candidate_name = hotel_id
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
            availability = check_availability(
                settings.xotelo_api_key,
                hotel_id=resolved_id,
                check_in_date=params["checkInDate"],
                check_out_date=params["checkOutDate"],
                guests=params["guests"],
                room_count=params["roomCount"],
            )
            rooms = availability.get("availableRooms") or []
            provider_links: dict[str, str] = {}
            if candidate_name and rooms:
                for room in rooms:
                    if room.get("bookingUrl"):
                        continue
                    room_name = str(room.get("roomName") or "")
                    provider = room_name.replace("Room via", "").strip()
                    if not provider:
                        continue
                    if provider not in provider_links:
                        query = f"{candidate_name} {provider} booking"
                        try:
                            result = _serper_post({"q": query})
                        except Exception:
                            logger.exception("booking link lookup failed for provider=%s", provider)
                            provider_links[provider] = ""
                        else:
                            top = _pick_first_organic(result)
                            provider_links[provider] = top.get("link") if top else ""
                    room["bookingUrl"] = provider_links.get(provider, "")
            return availability
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
        resolved_user_id = get_current_user_id() or userId
        logger.info(
            "create_booking_tool called: user_id=%s hotel_id=%s check_in_date=%s check_out_date=%s number_of_rooms=%s",
            resolved_user_id,
            hotelId,
            checkInDate,
            checkOutDate,
            numberOfRooms,
        )
        payload = {
            "userId": resolved_user_id,
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

        return create_booking(payload, resolved_user_id, settings.xotelo_api_key)

    @tool
    def booking_handoff_tool(
        hotel_name: str,
        city: str,
        check_in_date: str,
        check_out_date: str,
        guests: int = 2,
        room_count: int = 1,
    ) -> dict[str, Any]:
        """Provide booking provider links without completing a booking."""
        resolved_id = _resolve_hotel_id(None, hotel_name)
        if not resolved_id:
            return {"error": "Hotel not found. Provide a valid hotel name."}
        try:
            rates = fetch_room_rates(
                settings.xotelo_api_key,
                hotel_id=resolved_id,
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                guests=guests,
                room_count=room_count,
            )
        except Exception as exc:
            logger.exception("booking_handoff_tool failed")
            return {"error": str(exc)}

        deals = []
        for rate in rates:
            link = rate.get("link") or rate.get("url")
            deals.append(
                {
                    "provider": rate.get("name") or rate.get("provider"),
                    "price": rate.get("rate"),
                    "currency": rate.get("currency"),
                    "link": link,
                }
            )

        official_query = f"{hotel_name} {city} official site"
        official = None
        try:
            official_payload = _serper_post({"q": official_query})
            top = _pick_first_organic(official_payload)
            if top:
                official = {"title": top.get("title"), "url": top.get("link")}
        except Exception:
            logger.exception("booking_handoff_tool official site lookup failed")

        return {
            "hotelId": resolved_id,
            "hotelName": hotel_name,
            "officialSite": official,
            "deals": deals,
        }

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
        search_policy_web_tool,
        geocode_hotel_tool,
        search_hotels_tool,
        get_hotel_info_tool,
        create_booking_tool,
        booking_handoff_tool,
        check_hotel_availability_tool,
        get_weather_forecast_tool,
    ]
