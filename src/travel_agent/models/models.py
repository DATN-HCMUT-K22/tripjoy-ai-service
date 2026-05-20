from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional


@dataclass
class Coordinate:
    latitude: float
    longitude: float


@dataclass
class TravelRequest:
    destination_name: str
    coordinate: Coordinate
    travel_type: List[str]
    budget: int
    start_date: date
    end_date: date
    people_quantity: int
    suggest_locations: Optional[List[str]] = None


@dataclass
class Place:
    id: str
    types: List[str]
    location: Coordinate
    displayName: str
    primaryType: str
    reviews: List[str]


@dataclass
class OrToolPlace:
    index: int
    coordinate: Coordinate


@dataclass
class TravelNotebook:
    name: str
    food: str
    climate: str
    culture: str
    emergency_contacts: str


@dataclass
class TripItem:
    start_time: Optional[datetime] = None
    duration: Optional[int] = None
    note: Optional[str] = None
    location_name: Optional[str] = None
    place_id: Optional[str] = None


@dataclass
class FinalItinerary:
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    people_quantity: Optional[int] = None
    budget_estimate: Optional[int] = None
    themes: Optional[List[str]] = None
    destination: Optional[str] = None
    trip_items: Optional[List[TripItem]] = None


@dataclass
class ChatRequest:
    conversation_id: str
    message: str
    itinerary: Optional[FinalItinerary] = None


@dataclass
class ModifyItineraryRequest:
    itinerary_data: FinalItinerary
    unwanted_locations: List[TripItem]
    coordinate: Coordinate


@dataclass
class SuggestLocationsRequest:
    itinerary_data: FinalItinerary
    unwanted_location: TripItem
    coordinate: Coordinate


@dataclass(frozen=True)
class TrustScore:
    overall: float
    subscores: dict[str, float]
    reasons: dict[str, str]
