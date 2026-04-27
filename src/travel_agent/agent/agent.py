from travel_agent.agent.tools import tools
from travel_agent.agent.tool_executor import call_tool
from ..llm.llm_vertex import VertexLLM

def run_agent(message: str, conversation_id: str, system_prompt: str):
    llm = VertexLLM()

    messages = [
        {"role": "system",  "content": system_prompt},
        {"role": "user",    "content": message}
    ]

    for _ in range(3):
        response = llm.run_with_tools(messages, tools)

        if "tool_call" in response:
            tool_name = response["tool_call"]["name"]
            args      = response["tool_call"]["arguments"]
            args["conversation_id"] = conversation_id

            tool_result = call_tool(tool_name, args)

            # Append tool_call placeholder (để run_with_tools biết tên tool)
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_call": response["tool_call"]   # giữ nguyên để tra cứu tên
            })

            # Append tool result
            messages.append({
                "role": "tool",
                "content": str(tool_result)
            })

        else:
            return response["content"]

    return "Xin lỗi, tôi không xử lý được yêu cầu."