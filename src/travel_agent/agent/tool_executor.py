from travel_agent.agent.tool_registry import TOOLS

def call_tool(name: str, args: dict):
    if name not in TOOLS:
        raise Exception(f"Unknown tool: {name}")

    return TOOLS[name](**args)