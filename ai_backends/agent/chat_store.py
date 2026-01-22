from __future__ import annotations

from datetime import datetime, timezone
import json
import os
import threading
import uuid
from typing import Any

from langchain_core.messages import BaseMessage, messages_from_dict, messages_to_dict

_STORE_LOCK = threading.Lock()
_STORE_PATH = os.getenv(
    "CHAT_STORE_PATH",
    os.path.join(os.path.dirname(__file__), "data", "chat_sessions.json"),
)
_DEFAULT_TITLE = "Current Session"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_store_dir() -> None:
    os.makedirs(os.path.dirname(_STORE_PATH), exist_ok=True)


def _load_store() -> dict[str, Any]:
    if not os.path.exists(_STORE_PATH):
        return {"sessions": {}}
    try:
        with open(_STORE_PATH, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (json.JSONDecodeError, OSError):
        return {"sessions": {}}


def _save_store(store: dict[str, Any]) -> None:
    _ensure_store_dir()
    tmp_path = f"{_STORE_PATH}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as handle:
        json.dump(store, handle, ensure_ascii=True, indent=2)
    os.replace(tmp_path, _STORE_PATH)


_STORE: dict[str, Any] = _load_store()


def _ensure_session(session_id: str, user_id: str) -> dict[str, Any]:
    session = _STORE["sessions"].get(session_id)
    if session:
        return session
    session = {
        "sessionId": session_id,
        "userId": user_id,
        "title": _DEFAULT_TITLE,
        "uiMessages": [],
        "lcMessages": [],
        "createdAt": _now(),
        "updatedAt": _now(),
    }
    _STORE["sessions"][session_id] = session
    _save_store(_STORE)
    return session


def get_sessions_for_user(user_id: str) -> list[dict[str, Any]]:
    with _STORE_LOCK:
        sessions = [
            session
            for session in _STORE.get("sessions", {}).values()
            if session.get("userId") == user_id
        ]
        sessions.sort(key=lambda s: s.get("updatedAt", ""), reverse=True)
        return [
            {
                "id": session["sessionId"],
                "sessionId": session["sessionId"],
                "title": session.get("title", _DEFAULT_TITLE),
                "messages": list(session.get("uiMessages", [])),
            }
            for session in sessions
        ]


def get_langchain_messages(session_id: str, user_id: str) -> list[BaseMessage]:
    with _STORE_LOCK:
        session = _ensure_session(session_id, user_id)
        message_dicts = session.get("lcMessages", [])
    if not message_dicts:
        return []
    return messages_from_dict(message_dicts)


def set_langchain_messages(session_id: str, user_id: str, messages: list[BaseMessage]) -> None:
    with _STORE_LOCK:
        session = _ensure_session(session_id, user_id)
        session["lcMessages"] = messages_to_dict(messages)
        session["updatedAt"] = _now()
        _save_store(_STORE)


def append_ui_message(session_id: str, user_id: str, role: str, content: str) -> None:
    with _STORE_LOCK:
        session = _ensure_session(session_id, user_id)
        session["uiMessages"].append(
            {
                "id": uuid.uuid4().hex,
                "role": role,
                "content": content,
                "createdAt": _now(),
            }
        )
        session["updatedAt"] = _now()
        _save_store(_STORE)


def update_title_from_query(session_id: str, user_id: str, query: str) -> None:
    cleaned = (query or "").strip()
    if not cleaned:
        return
    trimmed = cleaned if len(cleaned) <= 20 else f"{cleaned[:20].rstrip()}..."
    with _STORE_LOCK:
        session = _ensure_session(session_id, user_id)
        current_title = session.get("title") or _DEFAULT_TITLE
        if current_title == _DEFAULT_TITLE:
            session["title"] = trimmed
            session["updatedAt"] = _now()
            _save_store(_STORE)
