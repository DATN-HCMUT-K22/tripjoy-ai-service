# Setup & Configuration Guide — TripJoy AI Service

## 1. Yêu cầu hệ thống

| Yêu cầu | Phiên bản tối thiểu | Ghi chú |
|---|---|---|
| Python | 3.12+ | Kiểm tra: `python --version` |
| pip | 24+ | Kiểm tra: `pip --version` |
| Docker | 24+ | Nếu deploy bằng container |
| Google Cloud SDK (`gcloud`) | Latest | Để auth Vertex AI |

---

## 2. Cấu hình môi trường local (Development)

### 2.1 Tạo virtual environment

```bash
cd tripjoy-ai-service

# Tạo venv
python -m venv .venv

# Kích hoạt (Linux/macOS)
source .venv/bin/activate

# Kích hoạt (Windows PowerShell)
.venv\Scripts\Activate.ps1
```

### 2.2 Cài đặt dependencies

```bash
# Production dependencies
pip install -r requirements.txt

# Dev dependencies (linting, testing)
pip install -r requirements-dev.txt
```

**Lưu ý về các package đặc biệt:**

| Package | Lý do cần | Ghi chú |
|---|---|---|
| `ortools` | Route optimization (TSP) | Cần gcc/g++ trên Linux |
| `wikipedia-api` | Lấy thông tin điểm đến cho notebook | Không cần API key |
| `vertexai` | Gemini model inference | Cần auth GCP |
| `google-cloud-aiplatform` | Vertex AI SDK | Cần VERTEX_PROJECT_ID |

### 2.3 Tạo file .env

```bash
cp .env.example .env
```

Điền các giá trị trong `.env`:

```bash
# === Google Vertex AI ===
VERTEX_PROJECT_ID=your-gcp-project-id
# Lấy từ GCP Console → Project ID (góc trên bên trái)

VERTEX_LOCATION=asia-southeast1
# Chọn region gần nhất. Gemini 1.5 Flash available ở:
# us-central1, europe-west1, asia-southeast1, asia-northeast1

VERTEX_MODEL=gemini-1.5-flash
# Hoặc: gemini-1.5-pro (chậm hơn nhưng chính xác hơn)

# === Google Places API (New) ===
GG_API_KEY=your-google-places-api-key
# Lấy từ: https://console.cloud.google.com/apis/credentials
# Enable "Places API (New)" — khác với "Places API" cũ

# === Internal Security ===
INTERNAL_API_KEY=tripjoy-internal-key
# Phải khớp với AI_SERVICE_API_KEY trong Spring Boot application.yaml
```

---

## 3. Xác thực Google Cloud (Vertex AI)

AI Service dùng **Application Default Credentials (ADC)** — đây là chuẩn của Google Cloud cho service-to-service auth.

### 3.1 Môi trường Local (Development)

```bash
# Cài Google Cloud SDK nếu chưa có
# https://cloud.google.com/sdk/docs/install

# Đăng nhập
gcloud auth login

# Thiết lập Application Default Credentials
gcloud auth application-default login

# Xác nhận đúng project
gcloud config set project YOUR_PROJECT_ID
```

### 3.2 Môi trường Docker / Production

Dùng **Service Account Key** thay vì user credentials:

```bash
# Bước 1: Tạo Service Account
gcloud iam service-accounts create tripjoy-ai-sa \
    --display-name="TripJoy AI Service Account"

# Bước 2: Gán quyền Vertex AI User
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:tripjoy-ai-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

# Bước 3: Tạo và tải key JSON
gcloud iam service-accounts keys create ./gcp-service-account.json \
    --iam-account="tripjoy-ai-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com"

# Bước 4: Set env var
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/gcp-service-account.json"
```

**Với Docker**, mount file key vào container:

```yaml
# docker-compose.yml
services:
  tripjoy-ai-service:
    environment:
      - GOOGLE_APPLICATION_CREDENTIALS=/app/secrets/gcp-sa.json
    volumes:
      - ./gcp-service-account.json:/app/secrets/gcp-sa.json:ro
```

> **QUAN TRỌNG:** Không commit file `gcp-service-account.json` lên Git. File này đã được thêm vào `.gitignore`.

---

## 4. Kích hoạt Google APIs cần thiết

Trên GCP Console hoặc qua `gcloud`:

```bash
# Vertex AI API (Gemini)
gcloud services enable aiplatform.googleapis.com

# Places API (New) — cho Google Places search
gcloud services enable places-backend.googleapis.com

# Wikipedia API không cần enable — là public API
```

---

## 5. Chạy service local

```bash
# Cách 1: Qua module (recommended)
python -m src.travel_agent.main

# Cách 2: Uvicorn trực tiếp (dev với auto-reload)
uvicorn travel_agent.api.server:app --host 0.0.0.0 --port 8000 --reload

# → API: http://localhost:8000
# → Swagger UI: http://localhost:8000/docs
# → ReDoc: http://localhost:8000/redoc
# → Health: http://localhost:8000/health
```

---

## 6. Deploy với Docker

### 6.1 Build image local

```bash
# Build production image
docker build -t tripjoy-ai-service:latest .

# Test image locally
docker run --env-file .env -p 8000:8000 tripjoy-ai-service:latest
```

### 6.2 Dùng docker-compose

```bash
# Tạo .env từ template
cp .env.example .env

# Chạy
docker-compose up -d

# Kiểm tra logs
docker-compose logs -f tripjoy-ai-service

# Kiểm tra health
curl http://localhost:8000/health
# → {"status":"ok","service":"tripjoy-ai-service","version":"1.0.0"}
```

### 6.3 Kết nối với TripJoy API (Spring Boot)

Nếu Spring Boot và AI Service chạy trên cùng server:

```yaml
# tripjoy-api docker-compose.yml — thêm external network
networks:
  backend:
    external: true
    name: tripjoy-ai-network   # Network của AI service
```

Cấu hình `application.yaml` của Spring Boot:

```yaml
ai:
  service:
    base-url: http://tripjoy-ai-service:8000  # Service name trong Docker network
    api-key: same-key-as-INTERNAL_API_KEY-in-ai-service-env
```

---

## 7. CI/CD Pipeline (GitHub Actions)

Xem file `.github/workflows/ai-service-ci.yml`. Pipeline gồm 4 jobs:

| Job | Trigger | Mô tả |
|---|---|---|
| `lint` | Mọi push/PR | Ruff linter + formatter + mypy |
| `test` | Sau lint pass | pytest unit tests |
| `build-and-push` | Push lên `main` | Build Docker image + push lên GHCR |
| `deploy` | Sau build pass | SSH deploy lên production server |

### 7.1 Cấu hình GitHub Secrets

Vào `GitHub repo → Settings → Secrets and variables → Actions`, thêm:

| Secret | Giá trị | Mô tả |
|---|---|---|
| `DEPLOY_HOST` | `your.server.ip` | IP của server production |
| `DEPLOY_USER` | `ubuntu` | SSH username |
| `DEPLOY_SSH_KEY` | `-----BEGIN...` | Private SSH key |
| `DEPLOY_PATH` | `/opt/tripjoy/ai-service` | Thư mục deploy trên server |

### 7.2 Cấu hình server production

```bash
# Trên server:
mkdir -p /opt/tripjoy/ai-service
cd /opt/tripjoy/ai-service

# Copy docker-compose.yml và .env lên server
scp docker-compose.yml user@server:/opt/tripjoy/ai-service/
scp .env user@server:/opt/tripjoy/ai-service/

# Login vào GitHub Container Registry
echo $GHCR_TOKEN | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

---

## 8. Kiểm tra Health & Debug

```bash
# Health check
curl http://localhost:8000/health

# Test generate itinerary (AI sẽ mất 5-30s)
curl -X POST http://localhost:8000/generate-itinerary \
  -H "Content-Type: application/json" \
  -H "X-Internal-Api-Key: tripjoy-internal-key" \
  -d '{
    "destination_name": "Đà Lạt",
    "travel_type": ["tourist_attraction"],
    "budget": "10000000",
    "start_date": "2025-03-01",
    "end_date": "2025-03-05",
    "people_quantity": 4,
    "coordinate": {"latitude": 11.9465, "longitude": 108.4419}
  }'

# Xem logs container
docker-compose logs -f --tail=100 tripjoy-ai-service
```

---

## 9. Troubleshooting

### Lỗi: `Missing Vertex AI configuration variables`

→ Kiểm tra `.env` có đủ `VERTEX_PROJECT_ID`, `VERTEX_LOCATION`, `VERTEX_MODEL`

### Lỗi: `google.api_core.exceptions.PermissionDenied`

→ Vertex AI API chưa được enable hoặc Service Account thiếu role `roles/aiplatform.user`

### Lỗi: `Google Places API error: 403`

→ `GG_API_KEY` sai hoặc chưa enable "Places API (New)"

### Lỗi: `ortools` không cài được trên Windows

```bash
# Windows cần Visual C++ Build Tools
# Tải từ: https://visualstudio.microsoft.com/downloads/ → Build Tools for Visual Studio
```

### Container khởi động chậm (~30s)

→ Bình thường — Vertex AI SDK cần thời gian khởi tạo. `start_period: 30s` trong healthcheck đã tính đến điều này.
