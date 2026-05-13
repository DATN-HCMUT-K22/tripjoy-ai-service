from travel_agent.mcp.db import get_db


def get_chat_message(conversation_id: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT 
            u.full_name AS sender_name, 
            m.message_content, 
            m.created_at AS sent_at
        FROM public.chat_message m
        JOIN public.users u 
            ON m.sender_id = u.id
        WHERE m.conversation_id = %s
        ORDER BY m.created_at ASC
    """,
        (conversation_id,),
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows


def get_distance_between_places(
    origin_place_id: str,
    destination_place_id: str,
    travel_mode: str = "DRIVE",
):
    """Tool: trả về khoảng cách (m) và thời gian (s) giữa 2 Google Place IDs."""

    # Import local tool implementation
    from travel_agent.tools.google_places import (
        get_distance_between_places as _get_distance,
    )

    return _get_distance(
        origin_place_id=origin_place_id,
        destination_place_id=destination_place_id,
        travel_mode=travel_mode,
    )
