from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Optional, Dict


@dataclass
class Coordinate:
    latitude: float
    longitude: float

@dataclass
class TravelRequest():
    destination_name: str
    coordinate: Coordinate
    travel_type: List[str]
    budget: str
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


@dataclass
class TripItem:
    start_time: datetime
    duration: int
    note: str
    location_name: str
    place_id: str

@dataclass
class FinalItinerary:
    name: str
    start_date: date
    end_date: date
    people_quantity: int
    budget_estimate: str
    themes: List[str]
    destination: str
    trip_items: List[TripItem]

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
