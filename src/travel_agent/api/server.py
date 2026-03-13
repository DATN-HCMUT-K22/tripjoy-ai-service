from fastapi import FastAPI
from pydantic import BaseModel
from datetime import date

from ..models.models import TravelRequest, FinalItinerary
from ..graphs.itinerary_graph import generate_itinerary, modify_itinerary
from ..graphs.notebook_graph import create_notebook
from ..graphs.chat_graph import chat


app = FastAPI(title="Travel AI Agent")


@app.post("/generate-itinerary")
def generate_itinerary_api(payload: TravelRequest):
    """
    API 1: Tạo FinalItinerary từ TravelRequest
    """
    itinerary = generate_itinerary(payload)
    
    if itinerary:
        return itinerary
    else:
        return {"error": "Failed to generate itinerary"}


@app.post("/generate-notebook")
def generate_notebook_api(itinerary_data: dict):
    """
    API 2: Tạo TravelNotebook từ FinalItinerary
    
    Nhận FinalItinerary object và trả về TravelNotebook
    """
    try:
        # Chuyển dict thành FinalItinerary object
        itinerary = FinalItinerary(
            name=itinerary_data.get("name", ""),
            description=itinerary_data.get("description", ""),
            start_date=itinerary_data.get("start_date"),
            end_date=itinerary_data.get("end_date"),
            people_quantity=itinerary_data.get("people_quantity", 1),
            budget_estimate=itinerary_data.get("budget_estimate", 0),
            themes=itinerary_data.get("themes", []),
            destination=itinerary_data.get("destination", ""),
            trip_items=itinerary_data.get("trip_items", [])
        )
        
        notebook = create_notebook(itinerary)
        
        if notebook:
            return notebook
        else:
            return {"error": "Failed to generate notebook"}
    except Exception as e:
        return {"error": f"Error processing itinerary: {str(e)}"}


@app.post("/modify-itinerary")
def modify_itinerary_api(itinerary_data: dict, unwanted_locations: list[str]):
    """
    API 3: Sửa lịch trình bằng cách thay thế các địa điểm không muốn đi
    
    Nhận FinalItinerary + danh sách unwanted_locations, trả về FinalItinerary mới đã sửa
    """
    try:
        # Chuyển dict thành FinalItinerary object
        itinerary = FinalItinerary(
            name=itinerary_data.get("name", ""),
            description=itinerary_data.get("description", ""),
            start_date=itinerary_data.get("start_date"),
            end_date=itinerary_data.get("end_date"),
            people_quantity=itinerary_data.get("people_quantity", 1),
            budget_estimate=itinerary_data.get("budget_estimate", 0),
            themes=itinerary_data.get("themes", []),
            destination=itinerary_data.get("destination", ""),
            trip_items=itinerary_data.get("trip_items", [])
        )
        
        # Sửa lịch trình
        modified_itinerary = modify_itinerary(itinerary, unwanted_locations)
        
        if modified_itinerary:
            return modified_itinerary
        else:
            return {"error": "Failed to modify itinerary"}
    except Exception as e:
        return {"error": f"Error modifying itinerary: {str(e)}"}


class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
def chat_api(payload: ChatRequest):
    """
    API 4: Chatbot du lịch
    
    Nhận câu hỏi từ người dùng, trả về phản hồi từ AI
    """
    try:
        response = chat(payload.message)
        
        if response:
            return {"message": response}
        else:
            return {"error": "Failed to get response"}
    except Exception as e:
        return {"error": f"Error in chat: {str(e)}"}
