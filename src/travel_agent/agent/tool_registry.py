# agent/tool_registry.py

from travel_agent.mcp.tools.query_chat_message import get_chat_message

TOOLS = {
    "get_chat_message": get_chat_message
}