"""
itinerary_graph.py - Tạo FinalItinerary từ TravelRequest
"""

import json
import re
from typing import List

from ..tools.mapbox_places import MapboxPlacesTool
from ..llm.llm_vertex import VertexLLM
from ..models.models import TravelRequest, FinalItinerary


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


def generate_itinerary(request: TravelRequest) -> FinalItinerary:
    """
    Tạo FinalItinerary trực tiếp từ TravelRequest bằng LLM
    Không fetch location, không bbox.
    LLM sẽ tự tạo lịch trình và trả về JSON đúng structure FinalItinerary.
    """
    llm = VertexLLM()

    print(f"\n--- Generating Itinerary for {request.destination_name} ---")

    prompt = f"""
Bạn là một Travel AI Planner chuyên nghiệp.

Hãy tạo một lịch trình du lịch chi tiết dựa trên thông tin sau:

Thông tin chuyến đi:
- Destination: {request.destination_name}
- Themes: {", ".join(request.travel_type)}
- Budget: {request.budget}
- Thời gian: {request.start_date} đến {request.end_date}
- Số người: {request.people_quantity}

YÊU CẦU:
1. Tạo lịch trình hợp lý theo số ngày thực tế.
2. Mỗi trip_item phải là 1 địa điểm cụ thể và phải có:
   - start_time (ISO format: YYYY-MM-DDTHH:MM:SS)
   - duration (phút)
   - note (mô tả hoạt động)
   - location_name (tên địa điểm cụ thể. Nhất định phải là 1 địa điểm cụ thể tồn tại trên google map, không được hoặc... Chỉ duy nhất 1 địa điểm)
3. Phân bổ thời gian hợp lý sáng / trưa / chiều / tối.
4. Ước tính budget phù hợp với ngân sách đầu vào.
5. Chỉ trả về JSON hợp lệ.
6. Không được dùng markdown code block.

JSON phải đúng format sau:

{{
  "name": "Tên chuyến đi hấp dẫn",
  "description": "Mô tả 2-3 câu về chuyến đi",
  "budget_estimate": 5000000,
  "themes": {request.travel_type},
  "trip_items": [
    {{
      "start_time": "2025-02-01T08:00:00",
      "duration": 120,
      "note": "Tham quan địa điểm nổi tiếng",
      "location_name": "Tên địa điểm"
    }}
  ]
}}
"""

    try:
        raw = llm.run(prompt)
        data = safe_json_loads(raw)

        trip_items = []
        for item in data.get("trip_items", []):
            trip_items.append({
                "start_time": item.get("start_time"),
                "duration": item.get("duration"),
                "note": item.get("note"),
                "location_name": item.get("location_name")
            })

        final_itinerary = FinalItinerary(
            name=data.get("name", "Chuyến đi thú vị"),
            description=data.get("description", ""),
            start_date=request.start_date,
            end_date=request.end_date,
            people_quantity=request.people_quantity,
            budget_estimate=float(data.get("budget_estimate", request.budget or 0)),
            themes=data.get("themes", request.travel_type),
            destination=request.destination_name,
            trip_items=trip_items
        )

        print(f"✓ Itinerary generated: {final_itinerary.name}")
        print(f"  Trip items: {len(final_itinerary.trip_items)}")

        return final_itinerary

    except Exception as e:
        print(f"✗ Error generating itinerary: {e}")
        return None


def modify_itinerary(itinerary: FinalItinerary, unwanted_locations: list[str]) -> FinalItinerary:
    """
    Sửa lịch trình bằng cách thay thế các địa điểm không muốn đi bằng địa điểm khác
    
    Args:
        itinerary: FinalItinerary object hoàn chỉnh
        unwanted_locations: Danh sách tên địa điểm khách hàng không muốn đi
    
    Returns:
        FinalItinerary: Lịch trình mới đã sửa
    """
    llm = VertexLLM()
    
    print("="*80)
    print("MODIFY ITINERARY")
    print("="*80)
    
    if not unwanted_locations:
        print("⚠ No locations to modify")
        return itinerary
    
    print(f"\n--- Modifying Itinerary ---")
    print(f"Unwanted locations: {unwanted_locations}")
    
    # Xác định các trip item cần thay thế
    trip_items_to_keep = []
    trip_items_to_replace = []
    
    for item in itinerary.trip_items:
        location_name = item.get("location_name", "")
        if location_name in unwanted_locations:
            trip_items_to_replace.append(item)
        else:
            trip_items_to_keep.append(item)
    
    print(f"Items to keep: {len(trip_items_to_keep)}")
    print(f"Items to replace: {len(trip_items_to_replace)}")
    
    if not trip_items_to_replace:
        print("⚠ No matching unwanted locations found")
        return itinerary
    
    # Chuẩn bị thông tin cho prompt
    kept_items_text = "\n".join([
        f"- {item.get('start_time')}: {item.get('location_name')} (Duration: {item.get('duration')} mins)"
        for item in trip_items_to_keep
    ])
    
    replace_items_text = "\n".join([
        f"- {item.get('start_time')}: {item.get('location_name')} (Duration: {item.get('duration')} mins, note: {item.get('note')})"
        for item in trip_items_to_replace
    ])
    
    prompt = f"""
Bạn là Travel AI Planner chuyên nghiệp.

Hãy sửa lịch trình du lịch bằng cách thay thế các địa điểm không mong muốn bằng địa điểm khác tương tự.

Thông tin chuyến đi:
- Destination: {itinerary.destination}
- Themes: {", ".join(itinerary.themes)}
- Budget: {itinerary.budget_estimate}
- Thời gian: {itinerary.start_date} đến {itinerary.end_date}
- Số người: {itinerary.people_quantity}

Các trip item giữ nguyên (KHÔNG được thay đổi):
{kept_items_text}

Các trip item cần thay thế (PHẢI thay thế bằng địa điểm khác tương tự):
{replace_items_text}

YÊU CẦU:
1. Chỉ thay thế các trip item trong danh sách "cần thay thế"
2. Không thay đổi các trip item "giữ nguyên"
3. Giữ nguyên start_time, duration, và cấu trúc của các trip item được thay thế
4. Mỗi trip item thay thế phải có:
   - start_time (giữ nguyên từ item cũ)
   - duration (giữ nguyên từ item cũ)
   - note (mô tả mới phù hợp với địa điểm mới)
   - location_name (địa điểm mới, phải là địa điểm cụ thể tồn tại)
5. Chỉ trả về JSON hợp lệ, không có markdown code block
6. JSON phải chứa TẤT CẢ trip items (cả giữ nguyên và thay thế)

JSON output:
{{
  "trip_items": [
    {{
      "start_time": "2025-02-01T08:00:00",
      "duration": 120,
      "note": "Mô tả hoạt động",
      "location_name": "Tên địa điểm"
    }},
    ...
  ]
}}
"""
    
    try:
        raw = llm.run(prompt)
        data = safe_json_loads(raw)
        
        new_trip_items = []
        for item in data.get("trip_items", []):
            new_trip_items.append({
                "start_time": item.get("start_time"),
                "duration": item.get("duration"),
                "note": item.get("note"),
                "location_name": item.get("location_name")
            })
        
        # Tạo FinalItinerary mới với trip items đã sửa
        modified_itinerary = FinalItinerary(
            name=itinerary.name,
            description=itinerary.description,
            start_date=itinerary.start_date,
            end_date=itinerary.end_date,
            people_quantity=itinerary.people_quantity,
            budget_estimate=itinerary.budget_estimate,
            themes=itinerary.themes,
            destination=itinerary.destination,
            trip_items=new_trip_items,
            travel_notebook=itinerary.travel_notebook  # Giữ notebook cũ
        )
        
        print(f"✓ Itinerary modified successfully")
        print(f"  New trip items: {len(modified_itinerary.trip_items)}")
        
        return modified_itinerary
        
    except Exception as e:
        print(f"✗ Error modifying itinerary: {e}")
        return itinerary


def create_itinerary(request: TravelRequest) -> FinalItinerary:
    """
    Main function: Tạo FinalItinerary từ TravelRequest
    
    Args:
        request: TravelRequest object
    
    Returns:
        FinalItinerary: Lịch trình chi tiết (chưa có travel_notebook)
    """
    print("="*80)
    print("CREATE ITINERARY")
    print("="*80)
    
    # Generate itinerary (combine fetch locations + generate in one step)
    itinerary = generate_itinerary(request)
    
    print("="*80)
    print(f"✓ Itinerary created successfully!")
    print("="*80)
    
    return itinerary
