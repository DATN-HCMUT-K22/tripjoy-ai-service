import json
import re
from typing import List
from datetime import date, datetime

from ..tools.google_places import search_nearby_places, get_place_by_id
from ..llm.llm_vertex import VertexLLM
from ..models.models import TravelRequest, FinalItinerary, OrToolPlace, Coordinate, TripItem

def places_to_text_block(places):
    blocks = []

    for p in places:

        block = f"""
    Name: {p.displayName}
    Type: {", ".join(p.types)}
    Place ID: {p.id}
    """
        
        blocks.append(block.strip())

    return "\n\n".join(blocks)

def reviews_to_text_block(reviews):
    blocks = []

    for key in reviews:

        block = f"""
    {key}: {reviews[key]}
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



def generate_itinerary_without_suggest_locations(request: TravelRequest) -> FinalItinerary:
    
    llm = VertexLLM()

    print(f"\n--- Generating Itinerary without suggestion for {request.destination_name} ---")

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
                
        prompt = f"""
Bạn là một AI Travel Planner.

QUY TẮC BẮT BUỘC:
- CHỈ trả về JSON hợp lệ và không markdown ```json
- KHÔNG được trả lời thêm bất kỳ text nào ngoài JSON đó
- Output phải bắt đầu bằng {{ và kết thúc bằng }}

Thông tin chuyến đi:
- Destination: {request.destination_name}
- Start date: {request.start_date}
- End date: {request.end_date}
- Budget: {request.budget} VND
- People: {request.people_quantity}
- Travel themes: {", ".join(request.travel_type)}

TOOL SẴN CÓ:
- get_distance_between_places(origin_place_id, destination_place_id, travel_mode="DRIVE")
  Trả về JSON:
  {{
    "distance_meters": <int>,
    "duration_seconds": <int>
  }}

Nhiệm vụ của bạn là làm theo thứ tự từng bước sau:
Bước 1: Chọn các địa điểm từ danh sách {places_text} để tôi có thể tham quan trong chuyến đi này (dựa trên thông tin chuyến đi)
Bước 2: Gọi tool get_distance_between_places để có dữ liệu về khoảng cách và thời gian di chuyển giữa các địa điểm và dựa vào đó sắp xếp các địa điểm để tối ưu quãng đường di chuyển giữa chúng.
Bước 3: Tạo TripItem cho từng địa điểm. Quy tắc tạo TripItem như sau:
- start_time của địa điểm đầu tiên bắt đầu từ {request.start_date}
- start_time của các địa điểm tiếp theo bằng start_time của địa điểm trước đó + duration của địa điểm trước đó + thời gian di chuyển giữa 2 địa điểm (số liệu cụ thể từ tool mà bạn đã gọi).
- Phân bố đều các địa điểm trong các ngày cho đến {request.end_date}
- duration tính bằng phút, location_name lấy từ Name

Format:
{{
  "trip_items": [
    {{
      "start_time": "2026-05-01T09:00:00",
      "duration": 120,
      "location_name": "place name"
    }}
  ]
}}
"""
        print("\n--- Generating itinerary ---")

        raw = llm.run(prompt)
        result = safe_json_loads(raw)
        # print(raw_response)

        name_to_id = {p.displayName: p.id for p in nearby_places}

        trip_items = []

        for item in result.get("trip_items", []):
            trip_items.append(
                TripItem(
                    start_time = datetime.fromisoformat(item["start_time"]),
                    duration = item["duration"],
                    note = None,
                    location_name = item["location_name"],
                    place_id = name_to_id.get(item["location_name"])
                )
            )
        
        reviews_map = {p.displayName: p.reviews for p in nearby_places}
        reviews_to_summarize = {item.location_name: reviews_map.get(item.location_name, []) for item in trip_items}

        reviews_text = reviews_to_text_block(reviews_to_summarize)
        # print(f"\n{reviews_text}\n")

        prompt2 = f"""
Dữ liệu đầu vào: {reviews_text}

Nhiệm vụ của bạn là Đọc các đánh giá thô (Value) và tóm tắt lại thành một đoạn văn phải đầy đủ ý, với giọng văn của người review bằng tiếng Việt (khoảng 2-3 câu).

YÊU CẦU ĐỊNH DẠNG ĐẦU RA (JSON ONLY):
Bạn phải trả về một JSON Object duy nhất và không markdown ```json, trong đó Key là tên địa điểm (giữ nguyên không thay đổi) và Value là đoạn tóm tắt bạn vừa viết.
KHÔNG được trả lời thêm bất kỳ text nào ngoài JSON đó.

Format:
{{
  "Tên địa điểm A": "Tóm tắt đánh giá A...",
  "Tên địa điểm B": "Tóm tắt đánh giá B..."
}}
"""
        raw2 = llm.run(prompt2)
        result2 = safe_json_loads(raw2)

        for item in trip_items:
            item.note = result2.get(item.location_name)
        
        itinerary = FinalItinerary(
            name=f"Trip to {request.destination_name}",
            start_date=request.start_date,
            end_date=request.end_date,
            people_quantity=request.people_quantity,
            budget_estimate=request.budget,
            themes=request.travel_type,
            destination=request.destination_name,
            trip_items=trip_items
        )

        return itinerary

    except Exception as e:
        print(f"✗ Error generating itinerary: {e}")
        return None
    

def generate_itinerary_with_suggest_locations(request: TravelRequest) -> FinalItinerary:
    
    llm = VertexLLM()

    print(f"\n--- Generating Itinerary with suggestion for {request.destination_name} ---")

    print("\n--- Step 1: Fetching places from Google Places API ---")
    
    try:
        suggest_locations = []
        for loc in request.suggest_locations:
            place = get_place_by_id(loc)
            if place:
                suggest_locations.append(place)
                print(f"✓ Found suggested location: {place.displayName}")

        suggest_text = places_to_text_block(suggest_locations)

        nearby_places = search_nearby_places(
            latitude=request.coordinate.latitude,
            longitude=request.coordinate.longitude,
            # included_types=request.travel_type
            included_types=["tourist_attraction"]
        )
        
        print(f"✓ Found {len(nearby_places)} places")
        
        # Chuẩn bị danh sách places cho prompt
        places_text = places_to_text_block(nearby_places)
                
        prompt = f"""
Bạn là một AI Travel Planner.

QUY TẮC BẮT BUỘC:
- CHỈ trả về JSON hợp lệ và không markdown ```json
- KHÔNG được trả lời thêm bất kỳ text nào ngoài JSON đó
- Output phải bắt đầu bằng {{ và kết thúc bằng }}

Thông tin chuyến đi:
- Destination: {request.destination_name}
- Start date: {request.start_date}
- End date: {request.end_date}
- Budget: {request.budget} VND
- People: {request.people_quantity}
- Travel themes: {", ".join(request.travel_type)}

TOOL SẴN CÓ:
- get_distance_between_places(origin_place_id, destination_place_id, travel_mode="DRIVE")
  Trả về JSON:
  {{
    "distance_meters": <int>,
    "duration_seconds": <int>
  }}

Nhiệm vụ của bạn là làm theo thứ tự từng bước sau:
Bước 1: Chuyến đi này bắt buộc phải có những địa điểm nằm trong {suggest_text} vì đó là những địa điểm tôi muốn đi. Ngoài ra, bạn phải chọn thêm các địa điểm từ danh sách {places_text} để tôi có thể tham quan trong chuyến đi này (dựa trên thông tin chuyến đi).
Bước 2: Gọi tool get_distance_between_places để có dữ liệu về khoảng cách và thời gian di chuyển giữa các địa điểm và dựa vào đó sắp xếp các địa điểm để tối ưu quãng đường di chuyển giữa chúng.
Bước 3: Tạo TripItem cho từng địa điểm. Quy tắc tạo TripItem như sau:
- start_time của địa điểm đầu tiên bắt đầu từ {request.start_date}
- start_time của các địa điểm tiếp theo bằng start_time của địa điểm trước đó + duration của địa điểm trước đó + thời gian di chuyển giữa 2 địa điểm (số liệu cụ thể từ tool mà bạn đã gọi).
- Phân bố đều các địa điểm trong các ngày cho đến {request.end_date}
- duration tính bằng phút, location_name lấy từ Name

Format:
{{
  "trip_items": [
    {{
      "start_time": "2026-05-01T09:00:00",
      "duration": 120,
      "location_name": "place name"
    }}
  ]
}}
"""
        print("\n--- Generating itinerary ---")

        raw = llm.run(prompt)
        print(f"Raw LLM output:\n{raw}\n")
        result = safe_json_loads(raw)
        # print(raw_response)

        name_to_id1 = {p.displayName: p.id for p in nearby_places}
        name_to_id2 = {p.displayName: p.id for p in suggest_locations}
        name_to_id = {**name_to_id1, **name_to_id2}

        trip_items = []

        for item in result.get("trip_items", []):
            trip_items.append(
                TripItem(
                    start_time = datetime.fromisoformat(item["start_time"]),
                    duration = item["duration"],
                    note = None,
                    location_name = item["location_name"],
                    place_id = name_to_id.get(item["location_name"])
                )
            )
        
        reviews_map1 = {p.displayName: p.reviews for p in nearby_places}
        reviews_map2 = {p.displayName: p.reviews for p in suggest_locations}
        reviews_map = {**reviews_map1, **reviews_map2}
        reviews_to_summarize = {item.location_name: reviews_map.get(item.location_name, []) for item in trip_items}

        reviews_text = reviews_to_text_block(reviews_to_summarize)
        # print(f"\n{reviews_text}\n")

        prompt2 = f"""
Dữ liệu đầu vào: {reviews_text}

Nhiệm vụ của bạn là Đọc các đánh giá thô (Value) và tóm tắt lại thành một đoạn văn phải đầy đủ ý, với giọng văn của người review bằng tiếng Việt (khoảng 2-3 câu).

YÊU CẦU ĐỊNH DẠNG ĐẦU RA (JSON ONLY):
Bạn phải trả về một JSON Object duy nhất và không markdown ```json, trong đó Key là tên địa điểm (giữ nguyên không thay đổi) và Value là đoạn tóm tắt bạn vừa viết.
KHÔNG được trả lời thêm bất kỳ text nào ngoài JSON đó.

Format:
{{
  "Tên địa điểm A": "Tóm tắt đánh giá A...",
  "Tên địa điểm B": "Tóm tắt đánh giá B..."
}}
"""
        raw2 = llm.run(prompt2)
        result2 = safe_json_loads(raw2)

        for item in trip_items:
            item.note = result2.get(item.location_name)
        
        itinerary = FinalItinerary(
            name=f"Trip to {request.destination_name}",
            start_date=request.start_date,
            end_date=request.end_date,
            people_quantity=request.people_quantity,
            budget_estimate=request.budget,
            themes=request.travel_type,
            destination=request.destination_name,
            trip_items=trip_items
        )

        return itinerary

    except Exception as e:
        print(f"✗ Error generating itinerary: {e}")
        return None


def generate_itinerary(request: TravelRequest) -> FinalItinerary:

    if request.suggest_locations:
        return generate_itinerary_with_suggest_locations(request)
    else:
        return generate_itinerary_without_suggest_locations(request)

def modify_itinerary(itinerary: FinalItinerary, unwanted_locations: List[TripItem], coordinate: Coordinate) -> FinalItinerary:

    llm = VertexLLM()
    
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

QUY TẮC BẮT BUỘC:
- CHỈ trả về JSON hợp lệ và không markdown ```json
- KHÔNG được trả lời thêm bất kỳ text nào ngoài JSON đó
- Output phải bắt đầu bằng {{ và kết thúc bằng }}

Thông tin chuyến đi:
- Destination: {itinerary.destination}
- Themes: {", ".join(itinerary.themes)}
- Budget: {itinerary.budget_estimate} VND
- Thời gian: {itinerary.start_date} đến {itinerary.end_date}
- Số người: {itinerary.people_quantity}

Nhiệm vụ của bạn là làm theo thứ tự từng bước sau:

Bước 1: Chọn các địa điểm từ danh sách {places_text} để thay thế cho các địa điểm trong {unwanted_locations_text} và không được trùng với các địa điểm đã có sẵn trong lịch trình {kept_locations_text}. Hãy chọn những địa điểm phù hợp với thông tin chuyến đi và có thể thay thế tốt cho các địa điểm không muốn đi.
Bước 2: Tạo TripItem cho từng địa điểm vừa được chọn thay thế. Quy tắc tạo TripItem như sau:
- start_time và duration của các TripItem mới giữ nguyên như các địa điểm bị thay thế để đảm bảo lịch trình không bị xáo trộn quá nhiều
- location_name lấy từ Name

Format:
{{
  "trip_items": [
    {{
      "start_time": "2026-05-01T09:00:00",
      "duration": 120,
      "location_name": "place name"
    }}
  ]
}}
"""
    
    try:
        raw = llm.run(prompt)
        data = safe_json_loads(raw)
        
        name_to_id = {p.displayName: p.id for p in nearby_places}
        name_to_reviews = {p.displayName: p.reviews for p in nearby_places}
        name_to_summarize = {item["location_name"]: name_to_reviews.get(item["location_name"], []) for item in data.get("trip_items", [])}
        reviews_text = reviews_to_text_block(name_to_summarize)
        
        prompt2 = f"""
Dữ liệu đầu vào: {reviews_text}

Nhiệm vụ của bạn là Đọc các đánh giá thô (Value) và tóm tắt lại thành một đoạn văn phải đầy đủ ý, với giọng văn của người review bằng tiếng Việt (khoảng 2-3 câu).

YÊU CẦU ĐỊNH DẠNG ĐẦU RA (JSON ONLY):
Bạn phải trả về một JSON Object duy nhất và không markdown ```json, trong đó Key là tên địa điểm (giữ nguyên không thay đổi) và Value là đoạn tóm tắt bạn vừa viết.
KHÔNG được trả lời thêm bất kỳ text nào ngoài JSON đó.

Format:
{{
  "Tên địa điểm A": "Tóm tắt đánh giá A...",
  "Tên địa điểm B": "Tóm tắt đánh giá B..."
}}
"""
        raw2 = llm.run(prompt2)
        data2 = safe_json_loads(raw2)

        suggest_trip_items = []
        for item in data.get("trip_items", []):
            suggest_trip_items.append(
                TripItem(
                    start_time = datetime.fromisoformat(item["start_time"]),
                    duration = item["duration"],
                    note = data2.get(item["location_name"]),
                    location_name = item["location_name"],
                    place_id = name_to_id.get(item["location_name"])
                )
            )

        i = 0
        unwanted_names = [loc.location_name for loc in unwanted_locations]
        for idx, item in enumerate(itinerary.trip_items):
            if item.location_name in unwanted_names:
                # Thay thế bằng TripItem mới từ LLM
                new_item = suggest_trip_items[i]
                itinerary.trip_items[idx] = TripItem(
                    start_time = new_item.start_time,
                    duration = new_item.duration,
                    note = new_item.note,
                    location_name = new_item.location_name,
                    place_id = new_item.place_id
                )
                i += 1
        
        return itinerary
        
    except Exception as e:
        print(f"✗ Error modifying itinerary: {e}")
        return itinerary


def suggest_location(itinerary: FinalItinerary, unwanted_location: TripItem, coordinate: Coordinate) -> list[TripItem]:

    llm = VertexLLM()
    
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

    kept_locations = [item for item in itinerary.trip_items if item.location_name != unwanted_location.location_name]
    kept_locations_text = trip_items_to_text(kept_locations)

    prompt = f"""
Bạn là Travel AI Planner chuyên nghiệp.

QUY TẮC BẮT BUỘC:
- CHỈ trả về JSON hợp lệ và không markdown ```json
- KHÔNG được trả lời thêm bất kỳ text nào ngoài JSON đó
- Output phải bắt đầu bằng {{ và kết thúc bằng }}

Thông tin chuyến đi:
- Destination: {itinerary.destination}
- Themes: {", ".join(itinerary.themes)}
- Budget: {itinerary.budget_estimate} VND
- Thời gian: {itinerary.start_date} đến {itinerary.end_date}
- Số người: {itinerary.people_quantity}

Nhiệm vụ của bạn như sau:

Chọn 5 địa điểm từ danh sách {places_text} để gợi ý thay thế cho địa điểm {unwanted_locations_text} và không được trùng với các địa điểm đã có sẵn trong lịch trình {kept_locations_text}. Hãy chọn những địa điểm phù hợp với thông tin chuyến đi và có thể thay thế tốt cho các địa điểm không muốn đi.

Format:
{{
  "trip_items": [
    {{
      "start_time": "2026-05-01T09:00:00",
      "duration": 120,
      "location_name": "place name"
    }}
  ]
}}
"""
    
    try:
        raw = llm.run(prompt)
        data = safe_json_loads(raw)

        name_to_id = {p.displayName: p.id for p in nearby_places}
        name_to_reviews = {p.displayName: p.reviews for p in nearby_places}
        name_to_summarize = {item["location_name"]: name_to_reviews.get(item["location_name"], []) for item in data.get("trip_items", [])}
        reviews_text = reviews_to_text_block(name_to_summarize)
        
        prompt2 = f"""
Dữ liệu đầu vào: {reviews_text}

Nhiệm vụ của bạn là Đọc các đánh giá thô (Value) và tóm tắt lại thành một đoạn văn phải đầy đủ ý, với giọng văn của người review bằng tiếng Việt (khoảng 2-3 câu).

YÊU CẦU ĐỊNH DẠNG ĐẦU RA (JSON ONLY):
Bạn phải trả về một JSON Object duy nhất và không markdown ```json, trong đó Key là tên địa điểm (giữ nguyên không thay đổi) và Value là đoạn tóm tắt bạn vừa viết.
KHÔNG được trả lời thêm bất kỳ text nào ngoài JSON đó.

Format:
{{
  "Tên địa điểm A": "Tóm tắt đánh giá A...",
  "Tên địa điểm B": "Tóm tắt đánh giá B..."
}}
"""
        raw2 = llm.run(prompt2)
        data2 = safe_json_loads(raw2)

        suggest_trip_items = []
        for item in data.get("trip_items", []):
            suggest_trip_items.append(
                TripItem(
                    start_time = datetime.fromisoformat(item["start_time"]),
                    duration = item["duration"],
                    note = data2.get(item["location_name"]),
                    location_name = item["location_name"],
                    place_id = name_to_id.get(item["location_name"])
                )
            )

        return suggest_trip_items

    except Exception as e:
        print(f"✗ Error suggesting trip item: {e}")
        return None


# if __name__ == "__main__":

#     print("\n=== TEST GENERATE ITINERARY ===\n")

#     # Tọa độ Đà Lạt
#     coordinate = Coordinate(
#         latitude=11.9,
#         longitude=108.4
#     )

#     # Mock request
#     request = TravelRequest(
#         destination_name="Da Lat",
#         coordinate=coordinate,
#         travel_type=["Food"],
#         budget="medium",
#         start_date=date(2026, 4, 30),
#         end_date=date(2026, 5, 3),
#         people_quantity=5
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