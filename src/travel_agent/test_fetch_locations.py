from dotenv import load_dotenv
load_dotenv()

from datetime import date
from src.travel_agent.graphs.itinerary_graph import node_fetch_locations
from src.travel_agent.graphs.state import TravelState
from src.travel_agent.models.models import TravelRequest


def main():
    # 1. Tạo request giả
    req = TravelRequest(
        origin_location="Hà Nội",
        destination_name="Đà Nẵng",
        travel_type=["du lịch", "ẩm thực"],
        budget="5 triệu",
        start_date=date(2025, 2, 1),
        end_date=date(2025, 2, 3),
        people_quantity=2
    )

    # 2. Tạo state
    state = TravelState(
        request=req,
        locations=[],
        itinerary=None,
        travel_notebook=None
    )

    # 3. Chạy node 1
    result_state = node_fetch_locations(state)

    # 4. In kết quả
    print("\n===== FETCH LOCATIONS RESULT =====")
    print(f"Total locations: {len(result_state.locations)}")
    for loc in result_state.locations[:5]:
        print(loc)


if __name__ == "__main__":
    main()
