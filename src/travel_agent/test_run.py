from dotenv import load_dotenv
load_dotenv()

from src.travel_agent.graphs.itinerary_graph import build_itinerary_graph
from src.travel_agent.graphs.state import TravelState
from src.travel_agent.models.models import TravelRequest


def main():
    graph = build_itinerary_graph()

    req = TravelRequest(
        origin_location="Hà Nội",
        destination_name="Đà Nẵng",
        travel_type=["family"],
        budget=5000000,
        people_quantity=2,
        start_date="2025-02-01",
        end_date="2025-02-05"
    )

    state = TravelState(request=req)

    # CHẠY GRAPH
    final_state = graph.invoke(state)

    print("===== RESULT =====")
    print(final_state.itinerary)

if __name__ == "__main__":
    main()
