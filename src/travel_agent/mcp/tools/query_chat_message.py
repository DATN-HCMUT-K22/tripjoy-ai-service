from travel_agent.mcp.db import get_db


def get_chat_message(conversation_id: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT 
            COALESCE(u.full_name, 'Trợ lý AI') AS sender_name, 
            m.message_content, 
            m.created_at AS sent_at
        FROM public.chat_message m
        LEFT JOIN public.users u 
            ON m.sender_id = u.id
        WHERE m.conversation_id = %s
        ORDER BY m.created_at ASC
    """,
        (conversation_id,),
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    if not rows:
        return "Không có tin nhắn nào trong cuộc trò chuyện này."

    formatted_messages = []
    for r in rows:
        sender = r.get("sender_name") or "Trợ lý AI"
        content = r.get("message_content") or ""
        sent_at = r.get("sent_at")
        time_str = (
            sent_at.strftime("%Y-%m-%d %H:%M:%S") if sent_at else "Không rõ thời gian"
        )
        formatted_messages.append(f"[{time_str}] {sender}: {content}")

    return "\n".join(formatted_messages)


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
