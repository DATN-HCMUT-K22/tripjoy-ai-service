# TripJoy AI Service

AI Service của hệ thống TripJoy — cung cấp các tính năng AI tạo lịch trình, sổ tay du lịch, và chatbot du lịch bằng Google Vertex AI (Gemini 1.5 Flash).

## 🚀 Quick Start

```bash
# 1. Clone và vào thư mục
cd tripjoy-ai-service

# 2. Tạo virtualenv
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows

# 3. Cài dependencies
pip install -r requirements.txt

# 4. Cấu hình môi trường
cp .env.example .env
# Điền các giá trị vào .env

# 5. Chạy service
python -m src.travel_agent.main
# → http://localhost:8000
# → Swagger UI: http://localhost:8000/docs
```

## 📁 Cấu trúc dự án

```
tripjoy-ai-service/
├── src/travel_agent/
│   ├── api/         # FastAPI endpoints (server.py)
│   ├── graphs/      # LangGraph AI logic
│   ├── llm/         # Vertex AI client
│   ├── models/      # Pydantic/Dataclass models
│   └── tools/       # Google Places, OR-Tools, Wikipedia
├── docs/            # Tài liệu kỹ thuật
├── tests/           # Unit tests
├── Dockerfile       # Multi-stage production build
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## 📚 Tài liệu

- [Setup & Configuration Guide](docs/SETUP_GUIDE.md)
- [Architecture Overview](docs/ARCHITECTURE.md)
- [API Reference](http://localhost:8000/docs) — Swagger UI (khi chạy local)

## 🔗 Tích hợp

AI Service được gọi **nội bộ** bởi Spring Boot backend (TripJoy API). Client KHÔNG gọi trực tiếp AI Service. Xem thêm tại [Architecture Overview](docs/ARCHITECTURE.md).
