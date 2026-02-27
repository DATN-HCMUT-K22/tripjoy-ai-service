from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Optional


@dataclass
class TravelRequest:
    destination_name: str
    travel_type: List[str]
    budget: str
    start_date: date
    end_date: date
    people_quantity: int


@dataclass
class TripItem:
    start_time: datetime
    duration: int
    note: str
    location_name: str
    # mapbox_id: str
    # photo_url: List[str]


@dataclass
class LocationTip:
    location_name: str
    tip: str

@dataclass
class TravelNotebook:
    name: str
    weather_forecast: str        # Dự báo thời tiết chung
    culture_etiquette: str       # Lưu ý văn hóa, ứng xử
    emergency_contacts: str      # Số cảnh sát, cứu thương, đại sứ quán
    packing_guide: str           # Nên mang quần áo gì    
    location_specific_tips: List[LocationTip] = field(default_factory=list)


@dataclass
class FinalItinerary:
    name: str
    description: str
    start_date: date
    end_date: date
    people_quantity: int
    budget_estimate: float
    themes: List[str]
    destination: str
    trip_items: List[dict]  
