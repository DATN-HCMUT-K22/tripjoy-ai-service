# src/travel_ai_agent/tools/base.py
from typing import Any


class BaseTool:
    name: str = "base_tool"

    def run(self, **kwargs: Any) -> Any:
        raise NotImplementedError
