from ..agent.agent import run_agent
from ..models.models import ChatRequest, FinalItinerary
from typing import Optional
from datetime import datetime, date


def build_system_prompt(
    conversation_id: str, itinerary: Optional[FinalItinerary] = None
) -> str:
    itinerary_text = ""

    if itinerary:
        lines = []
        if itinerary.name:
            lines.append(f"- Tên chuyến đi: {itinerary.name}")
        if itinerary.destination:
            lines.append(f"- Điểm đến: {itinerary.destination}")
        if itinerary.start_date:
            lines.append(f"- Ngày bắt đầu: {itinerary.start_date}")
        if itinerary.end_date:
            lines.append(f"- Ngày kết thúc: {itinerary.end_date}")
        if itinerary.people_quantity:
            lines.append(f"- Số người: {itinerary.people_quantity}")
        if itinerary.budget_estimate:
            lines.append(f"- Dự kiến ngân sách: {itinerary.budget_estimate} VND")
        if itinerary.themes:
            lines.append(f"- Chủ đề: {', '.join(itinerary.themes)}")
        if itinerary.trip_items:
            lines.append("- Các hoạt động trong lịch trình:")
            for item in itinerary.trip_items:
                time_str = ""
                if item.start_time:
                    if isinstance(item.start_time, (datetime, date)):
                        time_str = item.start_time.strftime("%d/%m/%Y %H:%M")
                    else:
                        time_str = str(item.start_time)
                
                location = item.location_name if item.location_name else "Chưa xác định địa điểm"
                note = f" ({item.note})" if item.note else ""
                duration = f" trong {item.duration} phút" if item.duration else ""
                
                lines.append(f"  + {time_str if time_str else 'Chưa định giờ'}{duration}: {location}{note}")
        itinerary_text = "\n".join(lines)

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
    system_prompt = build_system_prompt(
        chat_request.conversation_id, chat_request.itinerary
    )

    return run_agent(
        message=chat_request.message,
        conversation_id=chat_request.conversation_id,
        system_prompt=system_prompt,
    )
