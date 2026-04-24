import requests
import os
from typing import List
from dotenv import load_dotenv

from ..models.models import Place, Coordinate

load_dotenv()

GOOGLE_PLACES_API = "https://places.googleapis.com/v1/places:searchNearby"
GG_API_KEY = os.getenv("GG_API_KEY")


def _fetch_places(
    latitude: float,
    longitude: float,
    radius: int,
    included_types: List[str],
    max_reviews: int
) -> List[Place]:

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GG_API_KEY,
        "X-Goog-FieldMask": (
            "places.id,"
            "places.types,"
            "places.primaryType,"
            "places.displayName,"
            "places.location,"
            "places.reviews"
        ),
    }

    body = {
        "includedTypes": included_types,
        "maxResultCount": 20,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": latitude,
                    "longitude": longitude,
                },
                "radius": radius,
            }
        },
    }

    response = requests.post(GOOGLE_PLACES_API, headers=headers, json=body)

    if response.status_code != 200:
        raise Exception(f"Google Places API error: {response.text}")

    data = response.json()
    places_data = data.get("places", [])

    results: List[Place] = []

    for place in places_data:

        reviews = place.get("reviews", [])
        review_texts = []

        for r in reviews[:max_reviews]:
            text = r.get("originalText", {}).get("text")
            if text:
                review_texts.append(text)

        location_data = place.get("location", {})

        coordinate = Coordinate(
            latitude=location_data.get("latitude"),
            longitude=location_data.get("longitude")
        )

        place_obj = Place(
            id=place.get("id"),
            types=place.get("types", []),
            location=coordinate,
            displayName=place.get("displayName", {}).get("text"),
            primaryType=place.get("primaryType"),
            reviews=review_texts
        )

        results.append(place_obj)

    return results


def search_nearby_places(
    latitude: float,
    longitude: float,
    radius: int = 20000,
    included_types: List[str] = None,
    max_reviews: int = 5
) -> List[Place]:

    if included_types is None:
        included_types = ["tourist_attraction"]

    # offset ~20km
    lat_offset = 0.18
    lon_offset = 0.18

    grid_centers = [
        (latitude, longitude),  # center
        (latitude + lat_offset, longitude),  # north
        (latitude, longitude + lon_offset),  # east
    ]

    all_places = {}
    
    for lat, lon in grid_centers:

        places = _fetch_places(
            latitude=lat,
            longitude=lon,
            radius=radius,
            included_types=included_types,
            max_reviews=max_reviews
        )

        for p in places:
            all_places[p.id] = p

    return list(all_places.values())

def get_place_by_id(place_id: str, max_reviews: int = 5) -> Place:
    url = f"https://places.googleapis.com/v1/places/{place_id}"

    headers = {
        "X-Goog-Api-Key": GG_API_KEY,
        # KHÔNG có space sau dấu phẩy
        "X-Goog-FieldMask": (
            "id,"
            "types,"
            "primaryType,"
            "displayName,"
            "location,"
            "reviews"
        ),
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Google Places API error: {response.text}")

    data = response.json()

    # xử lý reviews
    reviews_data = data.get("reviews", [])
    review_texts = []

    for r in reviews_data[:max_reviews]:
        text = r.get("originalText", {}).get("text")
        if text:
            review_texts.append(text)

    # location
    location_data = data.get("location", {})

    coordinate = Coordinate(
        latitude=location_data.get("latitude"),
        longitude=location_data.get("longitude")
    )

    # build object
    place_obj = Place(
        id=data.get("id"),
        types=data.get("types", []),
        location=coordinate,
        displayName=data.get("displayName", {}).get("text"),
        primaryType=data.get("primaryType"),
        reviews=review_texts
    )

    return place_obj


# if __name__ == "__main__":

#     latitude = 11.9465
#     longitude = 108.4419

#     try:
#         places = search_nearby_places(
#             latitude=latitude,
#             longitude=longitude,
#             included_types=["tourist_attraction"],
#             max_reviews=3
#         )

#         print(f"\nFound {len(places)} places:\n")

#         for i, p in enumerate(places):

#             print("------------")
#             print(f"Place {i+1}")
#             print("ID:", p.id)
#             print("Name:", p.displayName)
#             print("Address:", p.formattedAddress)
#             print("Primary type:", p.primaryType)

#             if p.location:
#                 print(
#                     "Coordinate:",
#                     p.location.latitude,
#                     p.location.longitude
#                 )

#             print("Reviews:")

#             if not p.reviews:
#                 print("  No reviews")

#             for r in p.reviews:
#                 print(" -", r)

#         print("\nDone.")

#     except Exception as e:
#         print("Error:", e)