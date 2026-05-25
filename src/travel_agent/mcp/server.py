from mcp.server.fastmcp import FastMCP

from travel_agent.mcp.tools.query_chat_message import get_chat_message
from travel_agent.mcp.tools.distance_tool import get_distance_between_places

mcp = FastMCP("travel-agent")


@mcp.tool()
def get_chat_message_tool(conversation_id: str):
    """
    Lấy lịch sử hội thoại của conversation.
    """

    return get_chat_message(conversation_id)


@mcp.tool()
def get_distance_between_places_tool(
    origin_place_id: str,
    destination_place_id: str,
    travel_mode: str = "DRIVE",
):
    """
    Tính khoảng cách và thời gian giữa 2 địa điểm.
    """

    return get_distance_between_places(
        origin_place_id=origin_place_id,
        destination_place_id=destination_place_id,
        travel_mode=travel_mode,
    )


if __name__ == "__main__":
    mcp.run()