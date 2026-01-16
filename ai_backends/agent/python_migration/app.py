from __future__ import annotations

from datetime import datetime, timezone
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from config import Settings
from graph import build_graph

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

_session_memory: dict[str, dict] = {}


class ChatRequest(BaseModel):
    message: str
    sessionId: str | None = None


class ChatResponse(BaseModel):
    message: str


app = FastAPI(title="Travel Planner Agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
    max_age=84900,
)


def _wrap_user_message(user_message: str) -> str:
    now = datetime.now(timezone.utc).isoformat()
    return (
        f"User Name: {settings.user_name}\n"
        f"User ID: {settings.user_id}\n"
        f"UTC Time now:\n{now}\n\n"
        f"User Query:\n{user_message}"
    )


@app.post("/travelPlanner/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    session_id = request.sessionId or "default"
    state = _session_memory.get(session_id, {"messages": []})
    state["messages"].append(HumanMessage(content=_wrap_user_message(request.message)))

    result = agent_graph.invoke(state, config={"recursion_limit": 50})
    _session_memory[session_id] = result

    last_message = result["messages"][-1]
    return ChatResponse(message=last_message.content)
