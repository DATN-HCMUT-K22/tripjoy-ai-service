"""
chat_graph.py - Context-aware chatbot
"""

from ..llm.llm_vertex import VertexLLM
from typing import List, Dict
from ..models.models import ChatRequest, FinalItinerary


def build_prompt(message: str, recent_messages: List[Dict], itinerary: FinalItinerary) -> str:
    """
    Build prompt với context + memory
    """

    # format recent chat
    history_text = ""
    for m in recent_messages:
        role = "User" if m["role"] == "user" else "Assistant"
        history_text += f"{role}: {m['content']}\n"

    itinerary_text = ""
    if itinerary:
        itinerary_text = "\n".join([f"- {k}: {v}" for k, v in itinerary.items() if v])

    prompt = f"""
Bạn là TripJoy AI - trợ lý du lịch trong ứng dụng chat nhóm.

NGUYÊN TẮC TRẢ LỜI:
- Trả lời ngắn gọn (tối đa 2–3 câu)
- Tự nhiên như chat
- Không lan man

THÔNG TIN CHUYẾN ĐI (itinerary):
{itinerary_text if itinerary_text else "Chưa có"}

LỊCH SỬ HỘI THOẠI GẦN:
{history_text if history_text else "Không có"}

CÂU HỎI HIỆN TẠI:
{message}

Trả lời:
"""
    return prompt


def chat(chat_request: ChatRequest) -> str:
    """
    Chat có context + memory
    """

    llm = VertexLLM()

    # lấy last 6 messages
    recent_messages = chat_request.chat_history[-6:] if chat_request.chat_history else []

    prompt = build_prompt(chat_request.message, recent_messages, chat_request.itinerary)

    try:
        response = llm.run(prompt)
        return response.strip()
    except Exception as e:
        print(f"✗ Error in chatbot: {e}")
        return f"Xin lỗi, có lỗi xảy ra: {str(e)}"