from __future__ import annotations

from datetime import datetime, timezone
import logging

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from typing import Literal
import re

from config import Settings
from graph import build_graph
from booking.booking_routes import router as booking_router
from hotel.hotel_routes import router as hotel_router
from profile_routes import router as profile_router
from booking.booking_store import record_booking_summary

_root_logger = logging.getLogger()
if not _root_logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
else:
    _root_logger.setLevel(logging.INFO)

settings = Settings.from_env()
agent_graph = build_graph(settings)

class ChatRequest(BaseModel):
    message: str
    sessionId: str | None = None
    userId: str | None = None
    userName: str | None = None


class ChatResponse(BaseModel):
    message: str


app = FastAPI(title="Travel Planner Agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "x-user-id"],
    max_age=84900,
)
app.include_router(profile_router)
app.include_router(booking_router)
app.include_router(hotel_router)


def _wrap_user_message(user_message: str, user_id: str, user_name: str | None) -> str:
    now = datetime.now(timezone.utc).isoformat()
    resolved_user_id = user_id
    resolved_user_name = user_name or "Traveler"
    return (
        f"User Context (non-hotel identifiers): {resolved_user_name} ({resolved_user_id})\n"
        f"UTC Time now:\n{now}\n\n"
        f"User Query:\n{user_message}"
    )


def _parse_booking_summary(message: str) -> dict[str, str | int | list[dict[str, float | int | str]]] | None:
    if not message:
        return None
    booking_id_match = re.search(r"Booking ID:\s*([A-Za-z0-9-]+)", message)
    if not booking_id_match:
        return None
    booking_id = booking_id_match.group(1).strip()
    confirmation_match = re.search(r"Confirmation Number:\s*([A-Za-z0-9-]+)", message)
    check_in_match = re.search(r"Check-in Date:\s*(.+)", message)
    check_out_match = re.search(r"Check-out Date:\s*(.+)", message)
    guests_match = re.search(r"Number of Guests:\s*(\d+)", message)
    room_match = re.search(r"Room Type:\s*(.+)", message)
    total_match = re.search(r"Total Amount:\s*(.+)", message)
    hotel_match = re.search(
        r"booking at (.+?) has been confirmed",
        message,
        flags=re.IGNORECASE,
    )

    summary: dict[str, str | int | list[dict[str, float | int | str]]] = {
        "bookingId": booking_id,
    }
    if confirmation_match:
        summary["confirmationNumber"] = confirmation_match.group(1).strip()
    if check_in_match:
        summary["checkInDate"] = check_in_match.group(1).strip()
    if check_out_match:
        summary["checkOutDate"] = check_out_match.group(1).strip()
    if guests_match:
        summary["numberOfGuests"] = int(guests_match.group(1))
    if hotel_match:
        summary["hotelName"] = hotel_match.group(1).strip()
    if room_match:
        room_text = room_match.group(1).strip()
        summary["roomType"] = room_text
        provider_match = re.search(r"via\s+(.+)$", room_text, flags=re.IGNORECASE)
        if provider_match:
            summary["provider"] = provider_match.group(1).strip()
    if total_match:
        total_text = total_match.group(1).strip()
        amount_match = re.search(r"([0-9][0-9,]*(?:\\.[0-9]+)?)", total_text)
        nights_match = re.search(r"for\\s+(\\d+)\\s+night", total_text, flags=re.IGNORECASE)
        currency = None
        if "GBP" in total_text.upper() or "\u00a3" in total_text:
            currency = "GBP"
        elif "USD" in total_text.upper() or "$" in total_text:
            currency = "USD"
        elif "EUR" in total_text.upper() or "\u20ac" in total_text:
            currency = "EUR"
        if amount_match:
            amount = float(amount_match.group(1).replace(",", ""))
            nights = int(nights_match.group(1)) if nights_match else 0
            summary["pricing"] = [
                {
                    "totalAmount": amount,
                    "nights": nights,
                    "currency": currency or "USD",
                }
            ]
    return summary


@app.post("/travelPlanner/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    session_id = request.sessionId or "default"
    if not request.userId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="userId is required.",
        )
    user_id = request.userId
    wrapped_message = _wrap_user_message(
        request.message,
        user_id,
        request.userName,
    )
    thread_id = f"{user_id}:{session_id}"
    result = agent_graph.invoke(
        {"messages": [HumanMessage(content=wrapped_message)]},
        config={
            "recursion_limit": 50,
            "configurable": {"thread_id": thread_id},
        },
    )

    last_message = result["messages"][-1]
    summary = _parse_booking_summary(last_message.content)
    if summary:
        record_booking_summary(user_id, summary)
    return ChatResponse(message=last_message.content)
