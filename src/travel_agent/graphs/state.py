# src/travel_agent/graphs/state.py
from dataclasses import dataclass, field
from typing import List, Optional
from ..models.models import (
    TravelRequest,
    ItineraryPlan,
    TripItemPlan,
    LocationCandidate,
    TravelNotebook,
    FinalItinerary,
)

@dataclass
class TravelState:
    request: TravelRequest
    plan: Optional[ItineraryPlan] = None
    destination_candidates: List[LocationCandidate] = field(default_factory=list)
    matched_locations: List[LocationCandidate] = field(default_factory=list)
    location_embeddings: List[List[float]] = field(default_factory=list)
    item_embeddings: List[List[float]] = field(default_factory=list)
    matched_trip_items: List[TripItemPlan] = field(default_factory=list)
    travel_notebook: Optional[TravelNotebook] = None
    itinerary: Optional[FinalItinerary] = None
