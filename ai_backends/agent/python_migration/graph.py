from __future__ import annotations

import logging
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from config import Settings
from tools import build_tools

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are an assistant for planning trip itineraries of a hotel listing company. "
    "Help users plan their perfect trip, considering preferences and available hotels.\n\n"
    "Instructions:\n"
    "- Match hotels near attractions with user interests when prioritizing hotels.\n"
    "- You may plan itineraries with multiple hotels based on user interests and attractions.\n"
    "- Include the hotel and things to do for each day in the itinerary.\n"
    "- Use markdown formatting. Include hotel photos if available.\n"
    "- Always call get_user_profile_tool first to retrieve personalization data.\n"
    "- Always check availability before recommending a hotel.\n"
    "- If the user explicitly asks to book, call create_booking_tool using available hotel/room data.\n"
    "- If booking details are missing (hotelId, roomId, dates, guests, or primary guest contact info), "
    "ask a concise follow-up question instead of making up data.\n"
    "- Do not claim a booking failed unless the booking tool returns an error.\n"
    "- After a successful booking tool response, provide the final user response and do not call more tools."
)


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def build_graph(settings: Settings):
    tools = build_tools(settings)
    llm = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0.3,
    ).bind_tools(tools)

    def agent_node(state: AgentState) -> AgentState:
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        response = llm.invoke(messages)
        tool_calls = getattr(response, "tool_calls", None) or []
        if tool_calls:
            tool_names = [call.get("name") for call in tool_calls if isinstance(call, dict)]
            logger.info("agent_node decided to call tools: %s", tool_names)
        else:
            logger.info("agent_node returned a final response (no tool calls).")
        return {"messages": [response]}

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(tools))
    
    # Remove the mapping - tools_condition returns "tools" or END automatically
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")
    graph.set_entry_point("agent")

    return graph.compile()
