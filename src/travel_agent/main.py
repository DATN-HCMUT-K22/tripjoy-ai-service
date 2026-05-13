import uvicorn
from dotenv import load_dotenv
from pathlib import Path

# Load .env từ root của project (nơi chứa .env)
# Resolve absolute path để không phụ thuộc cwd khi chạy
_PROJECT_ROOT = Path(
    __file__
).parent.parent.parent  # main.py → travel_agent/ → src/ → tripjoy-ai-service/
load_dotenv(dotenv_path=_PROJECT_ROOT / ".env")

# Import settings SAU load_dotenv để Pydantic đọc đúng env vars
from travel_agent.config import get_settings  # noqa: E402


def run() -> None:
    settings = get_settings()

    uvicorn.run(
        "travel_agent.api.server:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_reload,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    run()
