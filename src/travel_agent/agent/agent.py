import json
import sys
import traceback

from google.genai.types import (
    GenerateContentConfig,
    Part,
)

from mcp import ClientSession
from mcp.client.stdio import (
    stdio_client,
    StdioServerParameters,
)

from travel_agent.llm.gemini_client import GeminiClient


MAX_TOOL_ITERATIONS = 10


async def run_agent(
    system_prompt: str,
    user_message: str,
):

    try:

        llm = GeminiClient()

        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "travel_agent.mcp.server"],
        )

        async with stdio_client(server_params) as (read, write):

            async with ClientSession(read, write) as session:

                # =====================================
                # INIT MCP SESSION
                # =====================================
                await session.initialize()

                tools = await session.list_tools()

                print("\n========== MCP TOOLS ==========")
                print(tools)
                print("================================\n")

                # =====================================
                # CREATE CHAT
                # =====================================
                chat = llm.client.aio.chats.create(
                    model=llm.model,

                    config=GenerateContentConfig(
                        system_instruction=system_prompt,

                        tools=[session],

                        temperature=0.2,

                        tool_config={
                            "function_calling_config": {
                                "mode": "AUTO"
                            }
                        }
                    )
                )

                # =====================================
                # FIRST USER MESSAGE
                # =====================================
                response = await chat.send_message(
                    user_message
                )

                final_texts = []

                # =====================================
                # TOOL LOOP
                # =====================================
                for iteration in range(MAX_TOOL_ITERATIONS):

                    print(
                        f"\n========== ITERATION {iteration + 1} =========="
                    )

                    candidate = response.candidates[0]

                    parts = candidate.content.parts

                    tool_called = False

                    for part in parts:

                        # =====================================
                        # TEXT RESPONSE
                        # =====================================
                        if part.text:

                            print("\n[MODEL TEXT]")
                            print(part.text)

                            final_texts.append(part.text)

                        # =====================================
                        # FUNCTION CALL
                        # =====================================
                        if part.function_call:

                            tool_called = True

                            function_call = part.function_call

                            tool_name = function_call.name

                            tool_args = dict(function_call.args)

                            print("\n[FUNCTION CALL]")
                            print("Tool:", tool_name)
                            print("Args:", tool_args)

                            # =====================================
                            # EXECUTE MCP TOOL
                            # =====================================
                            try:

                                tool_result = await session.call_tool(
                                    tool_name,
                                    arguments=tool_args,
                                )

                                print("\n[TOOL RESULT]")
                                print(tool_result)

                                # =====================================
                                # EXTRACT TOOL TEXT
                                # =====================================
                                tool_content = []

                                for item in tool_result.content:

                                    if hasattr(item, "text"):
                                        tool_content.append(item.text)

                                    else:
                                        tool_content.append(str(item))

                                tool_text = "\n".join(tool_content)

                            except Exception as tool_error:

                                traceback.print_exc()

                                tool_text = (
                                    f"Tool execution failed: {str(tool_error)}"
                                )

                            # =====================================
                            # SEND TOOL RESPONSE BACK TO GEMINI
                            # =====================================
                            response = await chat.send_message(
                                Part.from_function_response(
                                    name=tool_name,
                                    response={
                                        "result": tool_text
                                    }
                                )
                            )

                            # IMPORTANT:
                            # break để xử lý response mới
                            break

                    # =====================================
                    # NO TOOL CALL => DONE
                    # =====================================
                    if not tool_called:
                        break

                print("\n========== FINAL ANSWER ==========")

                final_response = "\n".join(final_texts)

                print(final_response)

                print("==================================\n")

                return final_response

    except Exception as e:

        traceback.print_exc()

        raise e