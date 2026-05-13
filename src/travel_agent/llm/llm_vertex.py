import os

import vertexai
from vertexai.generative_models import GenerativeModel, Tool, FunctionDeclaration

from travel_agent.config import get_settings


class VertexLLM:
    def __init__(self):
        settings = get_settings()

        # Nếu có service account credentials thì set trước khi init vertexai
        # Pydantic đã validate là absolute path và file tồn tại
        if settings.google_application_credentials:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
                settings.google_application_credentials
            )

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

    # def run_with_tools(self, messages, tools):
    #     """
    #     messages: [{"role": "...", "content": "..."}]
    #     tools: tool schema dạng dict
    #     """

    #     # 🔧 Convert tools → Gemini format
    #     function_declarations = []
    #     for t in tools:
    #         function_declarations.append(
    #             FunctionDeclaration(
    #                 name=t["name"],
    #                 description=t["description"],
    #                 parameters=t["parameters"],
    #             )
    #         )

    #     gemini_tools = [Tool(function_declarations=function_declarations)]

    #     # 🔧 Convert messages → Gemini format
    #     contents = []
    #     for m in messages:
    #         role = "user" if m["role"] == "user" else "model"

    #         if m.get("tool_call"):
    #             continue  # skip tool call placeholder

    #         contents.append({
    #             "role": role,
    #             "parts": [{"text": m["content"]}] if m["content"] else []
    #         })

    #     # 🔥 Call Gemini với tools
    #     response = self.model.generate_content(
    #         contents,
    #         tools=gemini_tools,
    #     )

    #     candidate = response.candidates[0]

    #     # 🔥 CASE 1: LLM muốn gọi tool
    #     try:
    #         part = candidate.content.parts[0]

    #         if hasattr(part, "function_call") and part.function_call:
    #             fc = part.function_call

    #             return {
    #                 "tool_call": {
    #                     "name": fc.name,
    #                     "arguments": dict(fc.args)
    #                 }
    #             }

    #     except Exception:
    #         pass

    #     # 🔥 CASE 2: trả lời bình thường
    #     try:
    #         return {
    #             "content": candidate.content.parts[0].text
    #         }
    #     except:
    #         return {
    #             "content": ""
    #         }

    def run_with_tools(self, messages, tools):
        # ── 1. Convert tools → Gemini FunctionDeclaration ──────────────
        function_declarations = []
        for t in tools:
            function_declarations.append(
                FunctionDeclaration(
                    name=t["name"],
                    description=t["description"],
                    parameters=t["parameters"],
                )
            )
        gemini_tools = [Tool(function_declarations=function_declarations)]

        # ── 2. Tách system prompt ra khỏi messages ───────────────────────
        system_instruction = None
        contents = []

        for m in messages:
            # System prompt → dùng system_instruction riêng của Gemini
            if m["role"] == "system":
                system_instruction = m["content"]
                continue

            # Tool result → Gemini dùng role "user" với part function_response
            if m["role"] == "tool":
                # Tìm tên tool từ message assistant liền trước
                tool_name = None
                for prev in reversed(messages[: messages.index(m)]):
                    if prev.get("tool_call"):
                        tool_name = prev["tool_call"]["name"]
                        break

                contents.append(
                    {
                        "role": "user",
                        "parts": [
                            {
                                "function_response": {
                                    "name": tool_name,
                                    "response": {"result": m["content"]},
                                }
                            }
                        ],
                    }
                )
                continue

            # Tool call placeholder → Gemini dùng role "model" với part function_call
            if m.get("tool_call"):
                contents.append(
                    {
                        "role": "model",
                        "parts": [
                            {
                                "function_call": {
                                    "name": m["tool_call"]["name"],
                                    "args": m["tool_call"]["arguments"],
                                }
                            }
                        ],
                    }
                )
                continue

            # Message thường (user / assistant)
            role = "user" if m["role"] == "user" else "model"
            if m.get("content"):
                contents.append({"role": role, "parts": [{"text": m["content"]}]})

        # ── 4. Gọi Gemini ───────────────────────────────────────────────
        response = self.model.generate_content(
            contents,
            tools=gemini_tools,
        )

        candidate = response.candidates[0]

        # ── 5. CASE 1: LLM muốn gọi tool ────────────────────────────────
        try:
            part = candidate.content.parts[0]
            if hasattr(part, "function_call") and part.function_call.name:
                fc = part.function_call
                return {"tool_call": {"name": fc.name, "arguments": dict(fc.args)}}
        except (IndexError, AttributeError) as e:
            print(f"[run_with_tools] Lỗi parse function_call: {e}")

        # ── 6. CASE 2: Trả lời bình thường ──────────────────────────────
        try:
            return {"content": candidate.content.parts[0].text}
        except (IndexError, AttributeError) as e:
            print(f"[run_with_tools] Lỗi parse text response: {e}")
            return {"content": ""}
