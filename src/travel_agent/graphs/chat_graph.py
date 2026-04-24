from ..agent.agent import run_agent
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

NGUYÊN TẮC TRẢ LỜI:
- Trả lời ngắn gọn, tự nhiên như chat nhóm
- Không lan man, không bịa thông tin

THÔNG TIN CHUYẾN ĐI:
{itinerary_text if itinerary_text else "Người dùng không cung cấp thông tin chuyến đi."}

CÔNG CỤ BẠN CÓ:
- get_chat_message(conversation_id): lấy lịch sử hội thoại

QUY TẮC GỌI TOOL:
- Nếu câu hỏi liên quan đến nội dung trước đó (ví dụ như tóm tắt cuộc hội thoại)→ GỌI NGAY get_chat_message, KHÔNG hỏi lại người dùng bất kỳ điều gì về ID cuộc hội thoại
- Người dùng hỏi bạn thì mặc định là người dùng nghĩ bạn sẽ đọc được lịch sử hội thoại, nên bạn cứ gọi get_chat_message để đọc rồi hiểu mà tư vấn cho người dùng nhé

Trả lời như một người bạn đang chat trong group.
"""


def chat(chat_request: ChatRequest) -> str:
    system_prompt = build_system_prompt(chat_request.conversation_id,chat_request.itinerary)

    print(system_prompt, )
    return run_agent(
        message=chat_request.message,
        conversation_id=chat_request.conversation_id,
        system_prompt=system_prompt
    )