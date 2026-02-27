"""
notebook_graph.py - Tạo TravelNotebook từ FinalItinerary
"""

import json
import re

from ..llm.llm_vertex import VertexLLM
from ..models.models import FinalItinerary, TravelNotebook, LocationTip


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
    """
    Tạo TravelNotebook từ FinalItinerary
    Bao gồm: thời tiết, văn hóa, emergency contacts, packing guide, location-specific tips
    
    Args:
        itinerary: FinalItinerary object chứa thông tin chuyến đi
    
    Returns:
        TravelNotebook: Hướng dẫn du lịch chi tiết
    """
    llm = VertexLLM()
    
    print(f"\n--- Generating Travel Notebook ---")
    
    # Lấy danh sách địa điểm từ trip_items
    locations = []
    if itinerary.trip_items:
        locations = [
            item.get("location_name", "")
            for item in itinerary.trip_items
            if item.get("location_name")
        ]
    
    locations_text = ", ".join(set(locations[:10]))  # Unique locations
    
    prompt = f"""
Bạn là một Travel Guide chuyên nghiệp có kinh nghiệm du lịch tại Việt Nam.

Tạo một Travel Notebook chi tiết cho chuyến du lịch sau:
- Điểm đến: {itinerary.destination}
- Thời gian: {itinerary.start_date} đến {itinerary.end_date}
- Số người: {itinerary.people_quantity}
- Ngân sách: {itinerary.budget_estimate}
- Các địa điểm chính: {locations_text}

Vui lòng cung cấp thông tin chi tiết dưới dạng JSON với cấu trúc sau:

{{
  "weather_forecast": "Mô tả chi tiết về thời tiết trong khoảng thời gian này, bao gồm nhiệt độ, độ ẩm, khả năng mưa, nên mang đồ gì",
  "culture_etiquette": "Những quy tắc văn hóa, tập quán địa phương cần biết khi du lịch ở địa điểm này",
  "emergency_contacts": "Danh sách các số điện thoại khẩn cấp quan trọng: bệnh viện, cảnh sát, đại sứ quán, v.v.",
  "packing_guide": "Danh sách đồ vật cần thiết để mang theo, dựa trên thời tiết và hoạt động",
  "location_specific_tips": [
    {{
      "location_name": "Tên địa điểm",
      "tip": "Mẹo, lưu ý hoặc thông tin thú vị về địa điểm này"
    }},
    {{
      "location_name": "Tên địa điểm",
      "tip": "Mẹo, lưu ý hoặc thông tin thú vị về địa điểm này"
    }}
  ]
}}

Trả về JSON HỢP LỆ, không có markdown code block.
"""

    try:
        raw = llm.run(prompt)
        data = safe_json_loads(raw)
        
        # Parse location tips
        location_tips = []
        if isinstance(data.get("location_specific_tips"), list):
            for tip_data in data.get("location_specific_tips", []):
                try:
                    location_tips.append(
                        LocationTip(
                            location_name=tip_data.get("location_name", ""),
                            tip=tip_data.get("tip", "")
                        )
                    )
                except Exception as e:
                    print(f"⚠ Error parsing tip: {e}")
        
        # Tạo TravelNotebook object
        notebook = TravelNotebook(
            name=f"Travel Notebook - {itinerary.destination}",
            weather_forecast=data.get("weather_forecast", "N/A"),
            culture_etiquette=data.get("culture_etiquette", "N/A"),
            emergency_contacts=data.get("emergency_contacts", "N/A"),
            packing_guide=data.get("packing_guide", "N/A"),
            location_specific_tips=location_tips
        )
        
        print(f"✓ Travel Notebook generated")
        print(f"  Location tips: {len(location_tips)}")
        
        return notebook
        
    except Exception as e:
        print(f"✗ Error generating notebook: {e}")
        return None


def create_notebook(itinerary: FinalItinerary) -> TravelNotebook:
    """
    Main function: Tạo TravelNotebook từ FinalItinerary
    
    Args:
        itinerary: FinalItinerary object
    
    Returns:
        TravelNotebook: Hướng dẫn du lịch chi tiết
    """
    print("="*80)
    print("CREATE TRAVEL NOTEBOOK")
    print("="*80)
    
    notebook = generate_notebook(itinerary)
    
    print("="*80)
    print(f"✓ Travel Notebook created successfully!")
    print("="*80)
    
    return notebook
