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