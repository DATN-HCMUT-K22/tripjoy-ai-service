# src/travel_ai_agent/main.py
import uvicorn
from dotenv import load_dotenv
load_dotenv()


def run():
    uvicorn.run("src.travel_agent.api.server:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    run()
