from fastapi import FastAPI
from pydantic import BaseModel
from datetime import date


from ..models.models import TravelRequest, FinalItinerary, ChatRequest, ModifyItineraryRequest, SuggestLocationsRequest
from ..graphs.itinerary_graph import generate_itinerary, modify_itinerary, suggest_location
from ..graphs.notebook_graph import generate_notebook
from ..graphs.chat_graph import chat


app = FastAPI(
    title="TripJoy AI Service",
    description="AI-powered travel itinerary generation — Google Vertex AI (Gemini)",
    version="1.0.0",
)


@app.get("/health", tags=["System"])
def health_check():
    """
    Lightweight health check — required by Docker HEALTHCHECK & load balancers.
    Returns 200 OK when service is running.
    """
    return {"status": "ok", "service": "tripjoy-ai-service", "version": "1.0.0"}


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
def generate_notebook_api(itinerary_data: FinalItinerary):
    """
    API 2: Tạo TravelNotebook từ FinalItinerary
    
    Nhận FinalItinerary object và trả về TravelNotebook
    """
    try:
        notebook = generate_notebook(itinerary_data)
        if notebook:
            return notebook
        else:
            return {"error": "Failed to generate notebook"}
    except Exception as e:
        return {"error": f"Error processing itinerary: {str(e)}"}


@app.post("/modify-itinerary")
def modify_itinerary_api(payload: ModifyItineraryRequest):
    """
    API 3: Sửa lịch trình bằng cách thay thế các địa điểm không muốn đi
    
    Nhận ModifyItineraryRequest (itinerary_data + unwanted_locations) trong body,
    trả về FinalItinerary mới đã sửa
    """
    try:        
        # Sửa lịch trình
        modified_itinerary = modify_itinerary(payload.itinerary_data, payload.unwanted_locations, payload.coordinate)
        
        if modified_itinerary:
            return modified_itinerary
        else:
            return {"error": "Failed to modify itinerary"}
    except Exception as e:
        return {"error": f"Error modifying itinerary: {str(e)}"}

@app.post("/suggest-locations")
def suggest_locations_api(payload: SuggestLocationsRequest):
    """
    API 4: Gợi ý các địa điểm thay thế cho các địa điểm không muốn đi

    Nhận SuggestLocationsRequest (itinerary_data + unwanted_locations) trong body,
    trả về danh sách các địa điểm gợi ý
    """
    try:
        # Gợi ý các địa điểm
        suggested_locations = suggest_location(payload.itinerary_data, payload.unwanted_location, payload.coordinate)

        if suggested_locations:
            return suggested_locations
        else:
            return {"error": "Failed to suggest locations"}
    except Exception as e:
        return {"error": f"Error suggesting locations: {str(e)}"}
    
@app.post("/chat")
def chat_api(payload: ChatRequest):
    """
    API 5: Chat với TripJoy AI

    Nhận ChatRequest (conversation_id + message + optional itinerary) trong body,
    trả về phản hồi từ TripJoy AI
    """
    try:
        response = chat(payload)
        return response
    except Exception as e:
        return {"error": f"Error processing chat: {str(e)}"}