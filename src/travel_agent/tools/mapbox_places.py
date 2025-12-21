import requests
import uuid
import os


class MapboxPlacesTool:
    BASE_URL = "https://api.mapbox.com/search/searchbox/v1/suggest"

    def search(self, text: str, limit: int = 20):
        token = os.getenv("MAPBOX_TOKEN")
        session_token = str(uuid.uuid4())

        params = {
            "q": text,
            "limit": limit,
            "session_token": session_token,
            "access_token": token,
        }

        res = requests.get(self.BASE_URL, params=params).json()
        suggestions = res.get("suggestions", [])

        out = []
        for s in suggestions:
            out.append({
                "id": s.get("mapbox_id"),
                "name": s.get("name"),
                "lat": s.get("coordinates", {}).get("latitude"),
                "lng": s.get("coordinates", {}).get("longitude"),
                "category": s.get("feature_type"),
            })

        return out
