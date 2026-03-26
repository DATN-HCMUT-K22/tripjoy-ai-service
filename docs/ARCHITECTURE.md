# Kiến Trúc TripJoy AI Service

## 1. Tổng quan

TripJoy AI Service là một **stateless FastAPI service** đóng vai trò tầng AI compute trong hệ thống TripJoy. Service không lưu dữ liệu vào database — mọi persistence đều do **Spring Boot backend** (TripJoy API) xử lý.

```
Mobile App / Web
      │
      │ JWT-authenticated HTTP
      ▼
┌─────────────────────┐
│  TripJoy API        │  ← Spring Boot (Java 21)
│  (Core Orchestrator)│    - Auth / Authorization
│                     │    - Database (PostgreSQL)
│  ① Validate request │    - Cache (Redis)
│  ② Call AI Service  │    - Business logic
│  ③ Save to DB       │
│  ④ Return response  │
└────────┬────────────┘
         │ Internal HTTP (X-Internal-Api-Key)
         │ POST /generate-itinerary, /chat, ...
         ▼
┌─────────────────────┐
│  TripJoy AI Service │  ← FastAPI (Python 3.12)
│  (Stateless Compute)│    - LangGraph graphs
│                     │    - Google Vertex AI (Gemini)
│  Nhận request       │    - Google Places API
│  Xử lý AI          │    - OR-Tools routing
│  Trả về JSON        │    - Wikipedia API
└─────────────────────┘
```

## 2. Luồng xử lý từng API

### 2.1 `POST /generate-itinerary` — Tạo lịch trình

```
TripJoy API
  │ POST /generate-itinerary { destination, dates, budget, coordinate }
  ▼
generate_itinerary() [itinerary_graph.py]
  │
  ├─ Step 1: Google Places API
  │    search_nearby_places(lat, lon, radius=20km)
  │    → Lấy danh sách Tourist Attractions (tối đa 20 địa điểm/lưới)
  │    → Grid search: center + north + east để phủ rộng hơn
  │
  ├─ Step 2: LLM (Gemini 1.5 Flash)
  │    Prompt: "Chọn địa điểm phù hợp, tạo TripItem cho từng ngày"
  │    → Output: JSON list of TripItems (start_time, duration, location_name, place_id, review)
  │
  └─ Step 3: Build FinalItinerary
       → name, start_date, end_date, people_quantity, budget_estimate, themes, trip_items
       → Return as JSON
```

### 2.2 `POST /modify-itinerary` — Sửa lịch trình

```
TripJoy API
  │ POST /modify-itinerary { itinerary_data: FinalItinerary, unwanted_locations: [...] }
  ▼
modify_itinerary() [itinerary_graph.py]
  │
  ├─ Phân loại TripItems: keep_list vs replace_list
  │    (dựa vào location_name có trong unwanted_locations không)
  │
  ├─ LLM (Gemini 1.5 Flash)
  │    Prompt: "Thay thế các địa điểm trong replace_list bằng địa điểm tương tự"
  │    → Giữ nguyên: start_time, duration
  │    → Thay đổi: location_name, note
  │
  └─ Build FinalItinerary mới + Return
```

### 2.3 `POST /generate-notebook` — Tạo sổ tay du lịch

```
TripJoy API
  │ POST /generate-notebook { FinalItinerary }
  ▼
generate_notebook() [notebook_graph.py]
  │
  ├─ Wikipedia API (vi → en fallback)
  │    get_destination_info(destination_name)
  │    → Lấy thông tin: food, climate, culture từ Wikipedia
  │
  ├─ LLM (Gemini 1.5 Flash)
  │    Prompt: "Tạo Travel Notebook dựa trên thông tin Wikipedia"
  │    → Output: JSON { summary, climate, culture }
  │
  └─ Build TravelNotebook { name, food, climate, culture } + Return
```

### 2.4 `POST /chat` — Chatbot du lịch

```
TripJoy API
  │ POST /chat { message, chat_history (last 6), itinerary? }
  ▼
chat() [chat_graph.py]
  │
  ├─ Build prompt từ: chat_history + itinerary context + message
  │
  ├─ LLM (Gemini 1.5 Flash)
  │    System: "Bạn là TripJoy AI - trả lời ngắn gọn (2-3 câu)"
  │    → Output: plain text response
  │
  └─ Return { message: "..." }
```

## 3. Cấu trúc code

```
src/travel_agent/
├── api/
│   └── server.py           # FastAPI app, route definitions, /health
│
├── graphs/                 # Business logic layer
│   ├── itinerary_graph.py  # generate_itinerary(), modify_itinerary()
│   ├── notebook_graph.py   # generate_notebook()
│   └── chat_graph.py       # chat(), build_prompt()
│
├── llm/
│   └── llm_vertex.py       # VertexLLM wrapper (Gemini via Vertex AI SDK)
│
├── models/
│   └── models.py           # Dataclass models:
│                           #   TravelRequest, FinalItinerary, TripItem,
│                           #   TravelNotebook, ChatRequest, ModifyItineraryRequest
│
└── tools/
    ├── google_places.py    # Google Places API v1 (searchNearby)
    ├── wiki_api.py         # Wikipedia API (vi + en)
    ├── or_tool.py          # Google OR-Tools TSP route optimization
    └── mapbox_places.py    # (Legacy — thay bằng google_places)
```

## 4. Technology Stack

| Layer | Technology | Mục đích |
|---|---|---|
| Web Framework | FastAPI 0.115 | Async REST API, auto Swagger docs |
| AI Model | Google Gemini 1.5 Flash (Vertex AI) | LLM inference |
| AI Orchestration | LangGraph 1.0 | Graph-based AI workflows |
| Places Search | Google Places API v1 (New) | Lấy danh sách địa điểm |
| Route Optimization | Google OR-Tools 9.11 | TSP — tối ưu thứ tự tham quan |
| Knowledge Source | Wikipedia API | Thông tin điểm đến |
| Runtime | Python 3.12 + Uvicorn | ASGI server |
| Container | Docker (multi-stage) | Production deployment |
| CI/CD | GitHub Actions | Lint → Test → Build → Deploy |

## 5. Security

### Internal API Key

AI Service được bảo vệ bởi `X-Internal-Api-Key` header. Spring Boot gửi header này với mỗi request:

```python
# server.py sẽ validate header này (TODO: implement middleware)
headers["X-Internal-Api-Key"] = INTERNAL_API_KEY
```

**Lưu ý:** Hiện tại chưa implement validation middleware. Trong production, thêm:

```python
from fastapi import Header, HTTPException
import os

async def verify_internal_key(x_internal_api_key: str = Header(...)):
    if x_internal_api_key != os.getenv("INTERNAL_API_KEY"):
        raise HTTPException(status_code=403, detail="Forbidden")
```

### GCP Authentication

Service dùng **Application Default Credentials (ADC)**:
- **Local**: `gcloud auth application-default login`
- **Production**: Service Account JSON mounted vào container

## 6. Scalability

AI Service là **stateless** — không lưu session hay state. Có thể scale ngang (horizontal scaling) bằng cách chạy nhiều instance sau một Load Balancer.

```
Load Balancer (Nginx/ALB)
├── ai-service:8000 (instance 1)
├── ai-service:8001 (instance 2)
└── ai-service:8002 (instance 3)
```

Thay đổi `workers` trong Dockerfile CMD:
```
--workers 2   # Chạy 2 processes trong 1 container
```

## 7. Limitations & Known Issues

| Vấn đề | Mô tả | Giải pháp đề xuất |
|---|---|---|
| Response time | LLM calls mất 5–30s | Spring Boot dùng WebClient async, không block thread |
| OR-Tools không dùng | `optimize_route()` đã import nhưng chưa integrate vào graph | Tích hợp sau step 1 Google Places |
| `place_id` trong `modify_itinerary` | Không trả về `place_id` trong `FinalItinerary` mới | LLM prompt cần thêm `place_id` field |
| Không có rate limiting | AI service có thể bị abuse | Rely vào Spring Boot rate limiting (Bucket4j) |
