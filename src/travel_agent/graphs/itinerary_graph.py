import json
import re
from typing import List
from datetime import date, datetime

from ..tools.mapbox_places import MapboxPlacesTool
from ..tools.google_places import search_nearby_places
from ..llm.llm_vertex import VertexLLM
from ..models.models import TravelRequest, FinalItinerary, OrToolPlace, Coordinate, TripItem
from ..tools.or_tool import optimize_route

def places_to_text_block(places):
    blocks = []

    for i, p in enumerate(places, start=0):

        reviews_text = "\n".join(
            [f"- {r}" for r in p.reviews[:5]]
        )

        block = f"""
Place {i}
Name: {p.displayName}
Type: {", ".join(p.types)}
Location: ({p.location.latitude}, {p.location.longitude})

Reviews:
{reviews_text}
"""

        blocks.append(block.strip())

    return "\n\n".join(blocks)

def ordered_places_to_prompt(places):
    blocks = []

    for i, p in enumerate(places):

        reviews_text = "\n".join([f"- {r}" for r in p.reviews[:5]])

        block = f"""
Place {i}
Name: {p.displayName}
Place ID: {p.id}

Reviews:
{reviews_text}
"""

        blocks.append(block.strip())

    return "\n\n".join(blocks)

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
    
    llm = VertexLLM()

    print(f"\n--- Generating Itinerary for {request.destination_name} ---")

    # TODO: Bước 1: Gọi hàm search_nearby_places để lấy danh sách locations
    print("\n--- Step 1: Fetching places from Google Places API ---")
    
    try:
        nearby_places = search_nearby_places(
            latitude=request.coordinate.latitude,
            longitude=request.coordinate.longitude,
            # included_types=request.travel_type
            included_types=["tourist_attraction"]
        )
        
        print(f"✓ Found {len(nearby_places)} places")
        
        # Chuẩn bị danh sách places cho prompt
        places_text = places_to_text_block(nearby_places)
        
        # print(f"\nAvailable places:\n{places_text}\n")
        
        # TODO: Bước 2: Xây dựng prompt để LLM chọn địa điểm từ danh sách
        prompt = f"""
Tôi có danh sách các địa điểm mà chúng tôi dự định sẽ ghé thăm.
{places_text}

Tôi cần bạn chọn cho tôi những địa điểm từ danh sách trên để tôi ghé thăm những địa điểm đó từ ngày {request.start_date} đến ngày {request.end_date} và phải phù hợp với các tiêu chí sau: ngân sách {request.budget}, số lượng {request.people_quantity} người, chủ đề du lịch {", ".join(request.travel_type)}.

Tôi chỉ cần bạn trả về 1 list chứa các số nguyên là id của từng địa điểm là được nhé.
Yêu cầu trả về dạng JSON hợp lệ, có cấu trúc như sau:
{{
  "selected_place_ids": [0,1,2]
}}
"""
        # Step 3: Gọi LLM để chọn địa điểm
        print("\n--- Step 2: Asking LLM to choose places ---")

        raw_response = llm.run(prompt)

        result = safe_json_loads(raw_response)

        place_indexes = result.get("selected_place_ids", [])

        if not place_indexes:
            print("⚠ LLM returned empty selection, using first 5 places")
            place_indexes = list(range(min(5, len(nearby_places))))

        # Map index → Place
        selected_places = []

        for idx in place_indexes:
            if isinstance(idx, int) and 0 <= idx < len(nearby_places):
                selected_places.append(nearby_places[idx])

        print(f"\n✓ Selected {len(selected_places)} places")
        
        or_tool_place = []
        for i, place in enumerate(selected_places):
            or_tool_place.append(OrToolPlace(index=i, coordinate=place.location))

        optimized_route = optimize_route(or_tool_place)
        ordered_places = [selected_places[i] for i in optimized_route]

        places_for_prompt = ordered_places_to_prompt(ordered_places)

        prompt2 = f"""
Bạn là một AI Travel Planner.

Hãy tạo các TripItem cho lịch trình du lịch.

Thông tin chuyến đi:

Start date: {request.start_date}

Danh sách địa điểm (đã tối ưu thứ tự di chuyển):

{places_for_prompt}

Yêu cầu:

- Mỗi địa điểm tạo ra 1 TripItem
- start_time bắt đầu từ 09:00 ngày {request.start_date}
- Các địa điểm tiếp theo tăng dần theo thời gian
- duration từ 60 đến 180 phút
- location_name lấy từ Name
- place_id lấy từ Place ID
- review là tóm tắt từ danh sách review của địa điểm (chuyển qua tiếng việt nhé)

⚠️ Chỉ trả JSON hợp lệ.

Format:

{{
  "trip_items": [
    {{
      "start_time": "2026-05-01T09:00:00",
      "duration": 120,
      "review": "tóm tắt từ danh sách review của địa điểm",
      "location_name": "place name",
      "place_id": "place id"
    }}
  ]
}}
"""
        
        print("\n--- Step 3: Generating itinerary ---")

        raw_response2 = llm.run(prompt2)

        result2 = safe_json_loads(raw_response2)

        itinerary = FinalItinerary(
        name=f"Trip to {request.destination_name}",
        start_date=request.start_date,
        end_date=request.end_date,
        people_quantity=request.people_quantity,
        budget_estimate=request.budget,
        themes=request.travel_type,
        destination=request.destination_name,
        trip_items=[]
    )

        for item in result2.get("trip_items", []):
            itinerary.trip_items.append(
                TripItem(
                    start_time=datetime.fromisoformat(item["start_time"]),
                    duration=item["duration"],
                    note=item["review"],
                    location_name=item["location_name"],
                    place_id=item["place_id"]
                )
            )
        return itinerary

    except Exception as e:
        print(f"✗ Error fetching places: {e}")
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
            trip_items=new_trip_items
        )
        
        print(f"✓ Itinerary modified successfully")
        print(f"  New trip items: {len(modified_itinerary.trip_items)}")
        
        return modified_itinerary
        
    except Exception as e:
        print(f"✗ Error modifying itinerary: {e}")
        return itinerary

# if __name__ == "__main__":

#     print("\n=== TEST GENERATE ITINERARY ===\n")

#     # Tọa độ Đà Lạt
#     coordinate = Coordinate(
#         latitude=11.9465,
#         longitude=108.4419
#     )

#     # Mock request
#     request = TravelRequest(
#         destination_name="Da Lat",
#         coordinate=coordinate,
#         travel_type=["tourist_attraction"],
#         budget="medium",
#         start_date=date(2026, 5, 1),
#         end_date=date(2026, 5, 3),
#         people_quantity=2
#     )

#     itinerary = generate_itinerary(request)

#     if not itinerary:
#         print("❌ Failed to generate itinerary")
#     else:

#         print("\n=== FINAL ITINERARY ===\n")

#         print("Trip name:", itinerary.name)
#         print("Destination:", itinerary.destination)
#         print("Start date:", itinerary.start_date)
#         print("End date:", itinerary.end_date)
#         print("People:", itinerary.people_quantity)

#         print("\n--- Trip Items ---\n")

#         for i, item in enumerate(itinerary.trip_items):

#             print(f"Stop {i+1}")
#             print("Time:", item.start_time)
#             print("Duration:", item.duration)
#             print("Location:", item.location_name)
#             print("Place ID:", item.place_id)
#             print("Note:", item.note)
#             print("----------------------")

#         print("\n✅ Done\n")