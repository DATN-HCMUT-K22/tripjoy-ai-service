"""
notebook_graph.py - Tạo TravelNotebook từ FinalItinerary
"""

import json
import re
from typing import List

from ..llm.llm_vertex import VertexLLM
from ..models.models import FinalItinerary, TravelNotebook
from ..tools.wiki_api import get_destination_info


def safe_json_loads(raw: str):
    """
    Làm sạch output của LLM và parse JSON an toàn.
    """
    if not raw:
        print("⚠ Warning: LLM returned empty string.")
        return {}

    try:
        raw = raw.strip()
        # Xóa markdown code block nếu có
        raw = re.sub(r"```json", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"```", "", raw)
        raw = raw.strip()
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"⚠ JSON Decode Error: {e}")
        return {}


def generate_notebook(itinerary: FinalItinerary) -> TravelNotebook:
    llm = VertexLLM()
    
    print(f"\n--- Generating Travel Notebook ---")
    
    # Lấy thông tin từ Wikipedia
    print(f"Fetching information from Wikipedia for {itinerary.destination}...")
    wiki_info = get_destination_info(itinerary.destination)
    
    prompt = f"""
Bạn là một Travel Guide chuyên nghiệp có kinh nghiệm du lịch tại Việt Nam.

Thông tin chuyến đi:
- Điểm đến: {itinerary.destination}
- Số người: {itinerary.people_quantity}
- Ngân sách: {itinerary.budget_estimate}

Thông tin từ Wikipedia về địa điểm du lịch {itinerary.destination}:
- Ẩm thực: {wiki_info.get('food', 'N/A')}
- Khí hậu: {wiki_info.get('climate', 'N/A')}
- Văn hóa: {wiki_info.get('culture', 'N/A')}

Nhiệm vụ của bạn là tạo một Travel Notebook cho chuyến du lịch dưới dạng JSON với cấu trúc sau:

{{
  "food": "Giới thiệu về ẩm thực địa phương, các món ăn đặc trưng, nhà hàng nổi tiếng và những trải nghiệm ẩm thực không thể bỏ qua",
  "climate": "Mô tả chi tiết về khí hậu: Hãy mô tả khí hậu vào thời điểm {itinerary.start_date} đến {itinerary.end_date} và đưa ra lời khuyên về trang phục và những thứ nên mang theo",
  "culture": "Những đặc điểm văn hóa nổi bật, tập quán địa phương, quy tắc ứng xử, lễ hội và sự kiện quan trọng"
}}

Lưu ý:
- Nếu thông tin từ wiki N/A ở field nào, hãy chủ động xây dựng nội dung cho field đó dựa vào các nguồn uy tín trên Internet
- Còn nếu những field từ wiki có nội dung đầy đủ, hãy chủ động xây dựng nội dung field đó theo thông tin từ wiki nhé

Trả về JSON HỢP LỆ, không có markdown code block.
"""
    
    try:
        raw = llm.run(prompt)
        data = safe_json_loads(raw)
        
        # Tạo TravelNotebook object
        notebook = TravelNotebook(
            name=f"Travel Notebook - {itinerary.destination}",
            food=data.get("food", "N/A"),
            climate=data.get("climate", "N/A"),
            culture=data.get("culture", "N/A")
        )
        
        print(f"✓ Travel Notebook generated")
        
        return notebook
        
    except Exception as e:
        print(f"✗ Error generating notebook: {e}")
        return None
