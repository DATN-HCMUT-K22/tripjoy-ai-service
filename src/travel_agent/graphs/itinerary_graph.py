# src/travel_agent/graphs/itinerary_graph.py

import json
import re
from datetime import datetime
from typing import List

# Không cần numpy và embedding nữa
from langgraph.graph import StateGraph, END

from ..graphs.state import TravelState
from ..tools.mapbox_places import MapboxPlacesTool
from ..llm.llm_vertex import VertexLLM
# from ..llm.embedding_vertex import VertexEmbedding  <-- Bỏ cái này
from ..models.models import (
    TripItemPlan,
    ItineraryPlan,
    TravelNotebook,
    FinalItinerary,
    LocationTip,
)


# ========= Helper: safe JSON parse từ LLM =========

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
        # In nhẹ log để debug nếu cần
        # print(f"Raw content: {raw[:100]}...") 
        return {}


# ========= NODE 1: LLM tạo plan (Entry Point) =========
# Thay vì search trước, ta cho LLM "sáng tác" lịch trình trước

def node_generate_plan(state: TravelState) -> TravelState:
    req = state.request
    llm = VertexLLM()

    print(f"--- Generating Plan for {req.destination_name} ---")

    prompt = f"""
Bạn là Travel AI Planner chuyên nghiệp.

Nhiệm vụ:
- Tạo một lịch trình du lịch chi tiết từ "{req.origin_location}" đến "{req.destination_name}".
- Themes (Chủ đề): {req.travel_type} (Phải tuân thủ đúng).
- Ngân sách: {req.budget}.
- Thời gian: {req.start_date} đến {req.end_date}.
- Số người: {req.people_quantity}.

YÊU CẦU QUAN TRỌNG:
1. Mỗi 'trip_item' phải có 'location_name' là tên địa điểm cụ thể, chính xác (Ví dụ: "Nhà hàng Ngon", "Dinh Độc Lập", "Bãi Đầm Trầu"). 
2. Đừng dùng tên chung chung như "Nhà hàng địa phương" hay "Quán cà phê".
3. Trả về JSON HỢP LỆ, không giải thích thêm.

Format JSON output:
{{
  "name": "Tên chuyến đi hấp dẫn",
  "description": "Mô tả ngắn gọn",
  "budget_estimate": 5000000,
  "themes": {req.travel_type},
  "destination": "{req.destination_name}",
  "trip_items": [
    {{
      "start_time": "2025-01-01T08:00:00",
      "duration": 120,
      "note": "Mô tả hoạt động...",
      "location_name": "Tên địa điểm cụ thể"
    }}
  ]
}}
"""

    raw = llm.run(prompt)
    data = safe_json_loads(raw)

    # Parse dữ liệu từ JSON sang Object
    trip_items: List[TripItemPlan] = []
    for ti in data.get("trip_items", []):
        try:
            start_time = datetime.fromisoformat(ti["start_time"])
        except ValueError:
            # Fallback nếu LLM sinh sai format ngày
            start_time = datetime.now()

        trip_items.append(
            TripItemPlan(
                start_time=start_time,
                duration=int(ti.get("duration", 60)),
                note=ti.get("note", ""),
                location_name=ti.get("location_name", "Địa điểm chưa xác định"),
                mapbox_id=None, # Chưa có ID, sẽ lấy ở bước sau
            )
        )

    state.plan = ItineraryPlan(
        name=data.get("name", "Chuyến đi thú vị"),
        description=data.get("description", ""),
        start_date=req.start_date,
        end_date=req.end_date,
        people_quantity=req.people_quantity,
        budget_estimate=float(data.get("budget_estimate", 0)),
        themes=list(data.get("themes", [])),
        destination=data.get("destination", req.destination_name),
        trip_items=trip_items,
    )

    return state


# ========= NODE 2: Resolve Mapbox Locations (Grounding) =========
# Search Mapbox dựa trên tên địa điểm LLM đã sinh ra

def node_resolve_locations(state: TravelState) -> TravelState:
    if state.plan is None:
        raise ValueError("Plan is missing")

    print("--- Resolving Mapbox IDs ---")
    
    tool = MapboxPlacesTool()
    resolved_items: List[TripItemPlan] = []
    
    # Destination context giúp search chính xác hơn 
    # (VD: search "Highlands Coffee" sẽ ra tiệm ở Sài Gòn thay vì Hà Nội)
    destination_context = state.plan.destination 

    for item in state.plan.trip_items:
        # Nếu tên quá chung chung hoặc rỗng thì bỏ qua
        if not item.location_name or item.location_name.lower() in ["khách sạn", "nhà hàng", "sân bay"]:
            resolved_items.append(item)
            continue

        # Tạo query: "Tên địa điểm + Tên thành phố du lịch"
        search_query = f"{item.location_name} {destination_context}"
        
        try:
            # Gọi Mapbox Search
            # Lưu ý: Hàm tool.search của bạn trả về list dict [{"id":..., "name":...}]
            results = tool.search(search_query, limit=1)
            
            if results:
                best_match = results[0]
                item.mapbox_id = best_match["id"]
                # Nếu model TripItemPlan có latitude/longitude thì gán luôn ở đây:
                # item.latitude = best_match["lat"]
                # item.longitude = best_match["lng"]
                print(f"Matched: '{item.location_name}' -> ID: {item.mapbox_id}")
            else:
                print(f"Not found: '{item.location_name}'")
                
        except Exception as e:
            print(f"⚠ Error searching '{item.location_name}': {e}")
        
        resolved_items.append(item)

    # Cập nhật lại danh sách đã có ID
    state.matched_trip_items = resolved_items
    return state


# ========= NODE 3: Generate Travel Notebook (Structured) =========

def node_generate_notebook(state: TravelState) -> TravelState:
    if state.plan is None:
        raise ValueError("Plan is missing")

    print("--- Generating Notebook ---")
    plan = state.plan
    llm = VertexLLM()
    
    # Lấy danh sách tên địa điểm (đã lọc trùng)
    loc_names = list(set([ti.location_name for ti in plan.trip_items if ti.location_name]))

    prompt = f"""
Bạn là chuyên gia du lịch.
Hãy tạo "Travel Notebook" cho chuyến đi đến "{plan.destination}".

Thông tin:
- Thời gian: {plan.start_date} đến {plan.end_date}.
- Địa điểm: {", ".join(loc_names)}

Yêu cầu Output JSON (Không Markdown):
{{
  "weather_forecast": "Dự báo thời tiết...",
  "culture_etiquette": "Lưu ý văn hóa...",
  "emergency_contacts": "Số điện thoại khẩn cấp...",
  "packing_guide": "Chuẩn bị hành lý...",
  "location_specific_tips": [
      {{ "location_name": "{loc_names[0] if loc_names else 'Địa điểm'}", "tip": "Mẹo..." }}
  ]
}}
"""
    try:
        raw = llm.run(prompt)
        data = safe_json_loads(raw)
    except Exception as e:
        print(f"Error gen notebook: {e}")
        data = {}

    # Map dữ liệu
    loc_tips = []
    for item in data.get("location_specific_tips", []):
        loc_tips.append(LocationTip(
            location_name=item.get("location_name", ""),
            tip=item.get("tip", "")
        ))

    notebook = TravelNotebook(
        name=f"Sổ tay du lịch {plan.destination}",
        weather_forecast=data.get("weather_forecast", "Đang cập nhật..."),
        culture_etiquette=data.get("culture_etiquette", ""),
        emergency_contacts=data.get("emergency_contacts", ""),
        packing_guide=data.get("packing_guide", ""),
        location_specific_tips=loc_tips
    )

    state.travel_notebook = notebook
    return state


# ========= NODE 4: Build Output =========

def node_build_output(state: TravelState) -> TravelState:
    print("--- Building Final Output ---")
    
    plan = state.plan
    notebook = state.travel_notebook
    
    # Fallback nếu notebook lỗi
    if not notebook:
        notebook = TravelNotebook(
            name="Sổ tay mặc định",
            weather_forecast="", culture_etiquette="", 
            emergency_contacts="", packing_guide="",
            location_specific_tips=[]
        )

    # Ưu tiên dùng danh sách đã resolve Mapbox ID
    final_items = state.matched_trip_items if state.matched_trip_items else plan.trip_items

    final = FinalItinerary(
        name=plan.name,
        description=plan.description,
        start_date=plan.start_date,
        end_date=plan.end_date,
        people_quantity=plan.people_quantity,
        budget_estimate=plan.budget_estimate,
        themes=plan.themes,
        origin_location=state.request.origin_location,
        destination=plan.destination,
        trip_items=final_items,
        travel_notebook=notebook,
    )

    state.itinerary = final
    return state


# ========= Build LangGraph =========

def build_itinerary_graph():
    graph = StateGraph(TravelState)

    # Đăng ký nodes
    graph.add_node("generate_plan", node_generate_plan)
    graph.add_node("resolve_locations", node_resolve_locations) # Node Mới
    graph.add_node("generate_notebook", node_generate_notebook)
    graph.add_node("build_output", node_build_output)

    # Entry Point: Bắt đầu bằng việc tạo kế hoạch luôn
    graph.set_entry_point("generate_plan")

    # Edges (Luồng đi mới)
    graph.add_edge("generate_plan", "resolve_locations")
    graph.add_edge("resolve_locations", "generate_notebook")
    graph.add_edge("generate_notebook", "build_output")
    graph.add_edge("build_output", END)

    return graph