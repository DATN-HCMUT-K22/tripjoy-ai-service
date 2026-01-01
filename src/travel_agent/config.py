# src/travel_ai_agent/config.py
import os
from dotenv import load_dotenv

load_dotenv()

env = os.getenv

# Vertex AI / Gemini
VERTEX_PROJECT_ID = env("VERTEX_PROJECT_ID")          
VERTEX_LOCATION = env("VERTEX_LOCATION", "us-central1")
VERTEX_MODEL = env("VERTEX_MODEL", "gemini-1.5-flash")

# Mapbox
MAPBOX_TOKEN = env("MAPBOX_TOKEN")

if not MAPBOX_TOKEN:
    raise RuntimeError("MAPBOX_TOKEN is not set in environment (.env)")
