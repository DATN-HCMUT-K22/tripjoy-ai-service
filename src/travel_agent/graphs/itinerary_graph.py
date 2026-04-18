import json
import re
from typing import List
from datetime import date, datetime

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
Place_id {p.id}
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

def trip_items_to_text(items: list[TripItem]) -> str:
    blocks = []

    for i, item in enumerate(items, start=1):
        block = f"""
Item {i}:
- Start time: {item.start_time.isoformat()}
- Duration: {item.duration} minutes
- Location: {item.location_name}
- Place ID: {item.place_id}
- Note: {item.note}
"""
        blocks.append(block.strip())

    return "\n\n".join(blocks)

def trip_item_to_text(item: TripItem) -> str:
    return f"""
Item:
- Start time: {item.start_time.isoformat()}
- Duration: {item.duration} minutes
- Location: {item.location_name}
- Place ID: {item.place_id}
- Note: {item.note}
"""


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
Bạn là một AI Travel Planner.

Thông tin chuyến đi:

- Destination: {request.destination_name}
- Start date: {request.start_date}
- End date: {request.end_date}
- Budget: {request.budget}
- People: {request.people_quantity}
- Travel themes: {", ".join(request.travel_type)}

Nhiệm vụ của bạn là làm theo thứ tự từng bước sau:

Bước 1: Chọn các địa điểm từ danh sách {places_text} để tôi có thể tham quan trong chuyến đi này (dựa trên thông tin chuyến đi)
Bước 2: Sắp xếp các địa điểm để tối ưu quãng đường di chuyển giữa chúng
Bước 3: Tạo TripItem cho từng địa điểm. Quy tắc tạo TripItem như sau:
- start_time bắt đầu từ {request.start_date}
- Các địa điểm tiếp theo tăng dần theo thời gian
- Phân bố đều các địa điểm trong các ngày cho đến {request.end_date}
- duration tính bằng phút
- location_name lấy từ Name
- place_id lấy từ Place ID
- review là tóm tắt từ danh sách review của địa điểm (viết bằng tiếng Việt) và đầy đủ ý từ các review gốc (bằng tiếng Anh) để tôi có thể hiểu rõ về địa điểm đó

⚠️ Chỉ trả về list các TripItem với JSON hợp lệ có Format như sau:
{{
  "trip_items": [
    {{
      "start_time": "2026-05-01T09:00:00",
      "duration": 120,
      "review": "tóm tắt review bằng tiếng Việt",
      "location_name": "place name",
      "place_id": "place id"
    }}
  ]
}}
"""
        print("\n--- Generating itinerary ---")

        raw_response = llm.run(prompt)

        # print("\n=== RAW LLM RESPONSE ===\n")
        # print(raw_response)
        # print("\n========================\n")

        result = safe_json_loads(raw_response)

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

        for item in result.get("trip_items", []):
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


def modify_itinerary(itinerary: FinalItinerary, unwanted_locations: List[TripItem], coordinate: Coordinate) -> FinalItinerary:

    llm = VertexLLM()
    
    print("="*80)
    print("MODIFY ITINERARY")
    print("="*80)
    
    if not unwanted_locations:
        print("⚠ No locations to modify")
        return itinerary
    
    print(f"\n--- Modifying Itinerary ---")
    
    nearby_places = search_nearby_places(
        latitude=coordinate.latitude,
        longitude=coordinate.longitude,
        # included_types=request.travel_type
        included_types=["tourist_attraction"]
    )

    places_text = places_to_text_block(nearby_places)

    unwanted_locations_text = trip_items_to_text(unwanted_locations)

    kept_locations = [item for item in itinerary.trip_items if item.location_name not in [loc.location_name for loc in unwanted_locations]]
    kept_locations_text = trip_items_to_text(kept_locations)

    prompt = f"""
Bạn là Travel AI Planner chuyên nghiệp.

Thông tin chuyến đi:
- Destination: {itinerary.destination}
- Themes: {", ".join(itinerary.themes)}
- Budget: {itinerary.budget_estimate}
- Thời gian: {itinerary.start_date} đến {itinerary.end_date}
- Số người: {itinerary.people_quantity}

Nhiệm vụ của bạn là làm theo thứ tự từng bước sau:

Bước 1: Chọn các địa điểm từ danh sách {places_text} để thay thế cho các địa điểm trong {unwanted_locations_text} và không được trùng với các địa điểm đã có sẵn trong lịch trình {kept_locations_text}. Hãy chọn những địa điểm phù hợp với thông tin chuyến đi và có thể thay thế tốt cho các địa điểm không muốn đi.
Bước 2: Tạo TripItem cho từng địa điểm vừa được chọn thay thế. Quy tắc tạo TripItem như sau:
- start_time và duration của các TripItem mới giữ nguyên như các địa điểm bị thay thế để đảm bảo lịch trình không bị xáo trộn quá nhiều
- location_name lấy từ Name
- place_id lấy từ Place ID
- review là tóm tắt từ danh sách review của địa điểm (viết bằng tiếng Việt) và đầy đủ ý từ các review gốc (bằng tiếng Anh) để tôi có thể hiểu rõ về địa điểm đó

⚠️ Chỉ trả về list các TripItem với JSON hợp lệ có Format như sau:
{{
  "trip_items": [
    {{
      "start_time": "2026-05-01T09:00:00",
      "duration": 120,
      "review": "tóm tắt review bằng tiếng Việt",
      "location_name": "place name",
      "place_id": "place id"
    }}
  ]
}}
"""
    
    try:
        raw = llm.run(prompt)
        data = safe_json_loads(raw)
        print("\n=== RAW LLM RESPONSE ===")
        print(raw)
        print("=== END RAW ===\n")

        print("\n=== PARSED DATA ===")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print("=== END DATA ===\n")
        
        i = 0
        unwanted_names = [loc.location_name for loc in unwanted_locations]
        for idx, item in enumerate(itinerary.trip_items):
            if item.location_name in unwanted_names:
                # Thay thế bằng TripItem mới từ LLM
                new_item = data["trip_items"][i]
                itinerary.trip_items[idx] = TripItem(
                    start_time=datetime.fromisoformat(new_item["start_time"]),
                    duration=new_item["duration"],
                    note=new_item["review"],
                    location_name=new_item["location_name"],
                    place_id=new_item["place_id"]
                )
                i += 1
        
        print(f"✓ Itinerary modified successfully")
        print(f"  New trip items: {len(itinerary.trip_items)}")

        return itinerary
        
    except Exception as e:
        print(f"✗ Error modifying itinerary: {e}")
        return itinerary


def suggest_location(itinerary: FinalItinerary, unwanted_location: TripItem, coordinate: Coordinate) -> FinalItinerary:

    llm = VertexLLM()
    
    print("="*80)
    print("SUGGEST LOCATION")
    print("="*80)
    
    if not unwanted_location:
        print("⚠ No locations to suggest")
        return itinerary

    print(f"\n--- Suggesting Locations ---")
    
    nearby_places = search_nearby_places(
        latitude=coordinate.latitude,
        longitude=coordinate.longitude,
        # included_types=request.travel_type
        included_types=["tourist_attraction"]
    )

    places_text = places_to_text_block(nearby_places)

    unwanted_locations_text = trip_item_to_text(unwanted_location)

    kept_locations = [item for item in itinerary.trip_items if item.location_name not in [loc.location_name for loc in unwanted_locations]]
    kept_locations_text = trip_items_to_text(kept_locations)

    prompt = f"""
Bạn là Travel AI Planner chuyên nghiệp.

Thông tin chuyến đi:
- Destination: {itinerary.destination}
- Themes: {", ".join(itinerary.themes)}
- Budget: {itinerary.budget_estimate}
- Thời gian: {itinerary.start_date} đến {itinerary.end_date}
- Số người: {itinerary.people_quantity}

Nhiệm vụ của bạn như sau:

Chọn 5 địa điểm từ danh sách {places_text} để gợi ý thay thế cho địa điểm {unwanted_locations_text} và không được trùng với các địa điểm đã có sẵn trong lịch trình {kept_locations_text}. Hãy chọn những địa điểm phù hợp với thông tin chuyến đi và có thể thay thế tốt cho các địa điểm không muốn đi.

⚠️ Chỉ trả về list các TripItem với JSON hợp lệ có Format như sau:
{{
  "trip_items": [
    {{
      "start_time": "2026-05-01T09:00:00",
      "duration": 120,
      "review": "tóm tắt review bằng tiếng Việt",
      "location_name": "place name",
      "place_id": "place id"
    }}
  ]
}}
"""
    
    try:
        raw = llm.run(prompt)
        data = safe_json_loads(raw)
        print("\n=== RAW LLM RESPONSE ===")
        print(raw)
        print("=== END RAW ===\n")

        print("\n=== PARSED DATA ===")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print("=== END DATA ===\n")
        
        new_items = data.get("trip_items", [])

        trip_item_list = []

        for item in new_items:
            trip_item = TripItem(
                start_time=datetime.fromisoformat(item["start_time"]),
                duration=item["duration"],
                note=item.get("review", ""),
                location_name=item.get("location_name", ""),
                place_id=item.get("place_id", "")
            )
            trip_item_list.append(trip_item)

        print(f"✓ Successfully")

        return trip_item_list

    except Exception as e:
        print(f"✗ Error suggesting trip item: {e}")
        return None


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