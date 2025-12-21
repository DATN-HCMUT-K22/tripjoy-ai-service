from fastapi import FastAPI
from pydantic import BaseModel
from datetime import date

from ..models.models import TravelRequest
from ..graphs.state import TravelState
from ..graphs.itinerary_graph import build_itinerary_graph


app = FastAPI(title="Travel AI Agent")

graph = build_itinerary_graph().compile()


class GenerateItineraryRequest(BaseModel):
    origin_location: str
    destination_name: str
    travel_type: list[str]
    budget: str
    start_date: date
    end_date: date
    people_quantity: int


@app.post("/generate-itinerary")
def generate_itinerary(payload: GenerateItineraryRequest):
    req = TravelRequest(
        origin_location=payload.origin_location,
        destination_name=payload.destination_name,
        travel_type=payload.travel_type,
        budget=payload.budget,
        start_date=payload.start_date,
        end_date=payload.end_date,
        people_quantity=payload.people_quantity,
    )

    state = TravelState(request=req)
    result = graph.invoke(state)

    return result["itinerary"]
