from vertexai.generative_models import (
    FunctionDeclaration,
    Tool,
    Part,
)

from travel_agent.agent.tools import tools
from travel_agent.agent.tool_executor import call_tool
from travel_agent.llm.llm_vertex import VertexLLM


# =========================================================
# CHAT AGENT
# =========================================================

def run_chat_agent(
    message: str,
    conversation_id: str,
    system_prompt: str,
):

    llm = VertexLLM()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message},
    ]

    for _ in range(3):

        response = llm.run_with_tools(messages, tools)

        if "tool_call" in response:

            tool_name = response["tool_call"]["name"]

            args = response["tool_call"]["arguments"]

            args["conversation_id"] = conversation_id

            tool_result = call_tool(
                tool_name,
                args
            )

            # assistant tool call
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_call": response["tool_call"]
            })

            # tool result
            messages.append({
                "role": "tool",
                "content": str(tool_result)
            })

        else:
            return response["content"]

    return "Xin lỗi, tôi không xử lý được yêu cầu."


# =========================================================
# ITINERARY AGENT
# =========================================================

def run_itinerary_agent(prompt: str):

    llm = VertexLLM()

    # ==========================================
    # Convert tools
    # ==========================================

    function_declarations = []

    for t in tools:

        function_declarations.append(
            FunctionDeclaration(
                name=t["name"],
                description=t["description"],
                parameters=t["parameters"],
            )
        )

    gemini_tools = [
        Tool(function_declarations=function_declarations)
    ]

    # ==========================================
    # Create chat session
    # ==========================================

    chat = llm.model.start_chat()

    # ==========================================
    # First prompt
    # ==========================================

    response = chat.send_message(
        prompt,
        tools=gemini_tools,
    )

    # ==========================================
    # Tool loop
    # ==========================================

    for _ in range(10):

        candidate = response.candidates[0]

        try:
            part = candidate.content.parts[0]

            # ==================================
            # TOOL CALL
            # ==================================

            if hasattr(part, "function_call") and part.function_call:

                fc = part.function_call

                tool_name = fc.name
                args = dict(fc.args)

                print("\n[TOOL CALL]")
                print(tool_name)
                print(args)

                # Execute tool
                tool_result = call_tool(
                    tool_name,
                    args
                )

                print("\n[TOOL RESULT]")
                print(tool_result)

                # Send function response back
                response = chat.send_message(
                    Part.from_function_response(
                        name=tool_name,
                        response={
                            "content": tool_result
                        }
                    )
                )

                continue

        except Exception as e:
            print(f"Tool handling error: {e}")

        # ==================================
        # FINAL TEXT
        # ==================================

        try:
            return candidate.content.parts[0].text
        except:
            return ""

    raise Exception("Max tool iterations reached")