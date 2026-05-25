from ..agent.agent import run_chat_agent
from ..models.models import ChatRequest, FinalItinerary
from typing import Optional


def build_system_prompt(conversation_id: str, itinerary: Optional[FinalItinerary] = None) -> str:
    itinerary_text = ""

    if itinerary:
        itinerary_text = "\n".join(
            [f"- {k}: {v}" for k, v in itinerary.items() if v]
        )

    return f"""
Bạn là TripJoy AI - trợ lý du lịch trong ứng dụng chat nhóm.

THÔNG TIN CHUYẾN ĐI:
{itinerary_text if itinerary_text else "Người dùng không cung cấp thông tin chuyến đi."}

CÔNG CỤ BẠN CÓ: get_chat_message(conversation_id): lấy lịch sử hội thoại

NGUYÊN TẮC TRẢ LỜI:
- Trước khi trả lời, phải luôn luôn gọi tool get_chat_message(conversation_id) để hiểu context cuộc hội thoại, sau đó mới trả lời người dùng.
- Trả lời ngắn gọn, tự nhiên như chat nhóm, không lan man, không bịa thông tin.
- Trả lời như một người bạn đang chat trong group.
"""


def chat(chat_request: ChatRequest) -> str:
    system_prompt = build_system_prompt(chat_request.conversation_id,chat_request.itinerary)

    return run_chat_agent(
        message=chat_request.message,
        conversation_id=chat_request.conversation_id,
        system_prompt=system_prompt
    )