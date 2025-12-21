import os
import json
from vertexai.generative_models import GenerativeModel


class VertexLLM:
    def __init__(self):
        project = os.getenv("VERTEX_PROJECT_ID")
        location = os.getenv("VERTEX_LOCATION")
        model_name = os.getenv("VERTEX_MODEL")

        if not (project and location and model_name):
            raise ValueError("Missing Vertex AI configuration variables")

        self.model = GenerativeModel(model_name)

    def run(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)

        # ALWAYS extract text properly
        if hasattr(response, "text") and response.text:
            return response.text

        try:
            return response.candidates[0].content.parts[0].text
        except:
            return ""
