import os

from google import genai

from travel_agent.config import get_settings


class GeminiClient:

    def __init__(self):

        settings = get_settings()

        if settings.google_application_credentials:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
                settings.google_application_credentials
            )

        self.client = genai.Client(
            vertexai=True,
            project=settings.vertex_project_id,
            location=settings.vertex_location,
        )

        self.model = settings.vertex_model