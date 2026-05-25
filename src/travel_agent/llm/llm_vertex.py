import os
import json
from pathlib import Path

import vertexai
from vertexai.generative_models import GenerativeModel, Tool, FunctionDeclaration

from travel_agent.config import get_settings


class VertexLLM:

    def __init__(self):
        settings = get_settings()

        # Nếu có service account credentials thì set trước khi init vertexai
        # Pydantic đã validate là absolute path và file tồn tại
        if settings.google_application_credentials:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.google_application_credentials

        # Init Vertex AI SDK với project và location
        vertexai.init(
            project=settings.vertex_project_id,
            location=settings.vertex_location,
        )

        self.model = GenerativeModel(settings.vertex_model)

    def run(self, prompt: str) -> str:
        """Gửi prompt đến Gemini và trả về text response."""
        response = self.model.generate_content(prompt)

        # Extract text an toàn
        if hasattr(response, "text") and response.text:
            return response.text

        try:
            return response.candidates[0].content.parts[0].text
        except (IndexError, AttributeError):
            return ""
    