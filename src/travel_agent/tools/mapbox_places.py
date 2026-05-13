import requests
import uuid
import os


class MapboxPlacesTool:
    BASE_URL = "https://api.mapbox.com/search/searchbox/v1/suggest"
    RETRIEVE_URL = "https://api.mapbox.com/search/searchbox/v1/retrieve"

    def search(self, text: str, proximity: str = None):
        token = os.getenv("MAPBOX_TOKEN")
        session_token = str(uuid.uuid4())

        params = {
            "q": text,
            "proximity": proximity,
            "limit": 10,
            "session_token": session_token,
            "access_token": token,
        }

        res = requests.get(self.BASE_URL, params=params)
        res.raise_for_status()

        return res.json()

    def retrieve(self, mapbox_id: str):
        token = os.getenv("MAPBOX_TOKEN")
        session_token = str(uuid.uuid4())

        url = f"{self.RETRIEVE_URL}/{mapbox_id}"
        params = {
            "session_token": session_token,
            "access_token": token,
        }

        res = requests.get(url, params=params)
        res.raise_for_status()

        return res.json()
