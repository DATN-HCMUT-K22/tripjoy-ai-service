from ..agent.agent import run_agent
from ..models.models import ChatRequest, FinalItinerary
from typing import Optional


def build_system_prompt(conversation_id: str, message: str, itinerary: Optional[FinalItinerary] = None) -> str:
    itinerary_text = ""

    if itinerary:
        itinerary_text = "\n".join(
            [f"- {k}: {v}" for k, v in itinerary.items() if v]
        )

    return f"""
Bạn là TripJoy AI - trợ lý du lịch trong ứng dụng chat nhóm.

THÔNG TIN CHUYẾN ĐI:
{itinerary_text if itinerary_text else "Người dùng không cung cấp thông tin chuyến đi."}

CONVERSATION ID HIỆN TẠI:
{conversation_id}

Bạn KHÔNG có quyền truy cập lịch sử chat
nếu chưa gọi tool.

TOOLS:
- get_chat_message_tool(conversation_id)

QUY TẮC BẮT BUỘC:

Nếu người dùng hỏi:
- lịch sử chat
- tóm tắt hội thoại
- mọi người đã nói gì
- cuộc trò chuyện trước đó
- context nhóm

THÌ PHẢI gọi:

get_chat_message_tool(
    conversation_id="{conversation_id}"
)

trước khi trả lời.

Không được tự suy đoán dữ liệu chat.
"""

def chat(chat_request: ChatRequest) -> str:
    system_prompt = build_system_prompt(chat_request.conversation_id, chat_request.message, chat_request.itinerary)

    return run_agent(
        system_prompt=system_prompt,
        user_message=chat_request.message
    )