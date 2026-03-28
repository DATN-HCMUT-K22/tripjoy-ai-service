# ============================================================
# config.py — TripJoy AI Service Configuration
# Enterprise Best Practice: Pydantic Settings
#
# - Tất cả config đọc từ environment variables (12-Factor App)
# - Validation tự động khi khởi động — fail-fast nếu thiếu biến bắt buộc
# - Không hardcode giá trị mặc định cho secrets
# - Dùng Settings singleton (get_settings) để tránh đọc .env nhiều lần
# ============================================================
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Root của project (tripjoy-ai-service/)
# Dùng để load .env từ đúng vị trí bất kể cwd khi chạy
_PROJECT_ROOT = Path(__file__).parent.parent.parent  # src/travel_agent/ → src/ → tripjoy-ai-service/


class Settings(BaseSettings):
    """
    Cấu hình của TripJoy AI Service.

    CHUẨN: 12-Factor App — mọi config đều đến từ environment variables.
    Thứ tự ưu tiên (cao → thấp):
      1. Environment variables của hệ thống (export FOO=bar)
      2. .env file ở root project (chỉ dùng trong development)
      3. Giá trị default trong class (chỉ dùng cho non-secret settings)
    """

    model_config = SettingsConfigDict(
        env_file=str(_PROJECT_ROOT / ".env"),   # Load từ root, không phải src/
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",                          # Bỏ qua env vars không dùng (tránh crash)
    )

    # ── Vertex AI / Gemini (BẮT BUỘC) ─────────────────────────
    vertex_project_id: str = Field(
        ...,  # `...` = bắt buộc, không có default
        description="GCP project ID (ví dụ: my-project-123)",
    )
    vertex_location: str = Field(
        default="asia-southeast1",
        description="GCP region chứa Vertex AI endpoint",
    )
    vertex_model: str = Field(
        default="gemini-2.5-flash",
        description="Tên Gemini model trên Vertex AI",
    )

    # ── Google Application Credentials (BẮT BUỘC cho production) ─
    # Trong development: dùng `gcloud auth application-default login`
    # Trong production/Docker: set biến này trỏ đến file JSON được mount vào container
    # QUAN TRỌNG: KHÔNG đặt file JSON trong source tree
    google_application_credentials: str | None = Field(
        default=None,
        description=(
            "Absolute path đến GCP Service Account JSON key. "
            "Production: mount file vào container, set biến này. "
            "Development: để trống nếu đã `gcloud auth application-default login`."
        ),
    )

    # ── Google Places API ──────────────────────────────────────
    gg_api_key: str | None = Field(
        default=None,
        description="Google Places API key (Places API v1 New)",
    )

    # ── Mapbox (Legacy — dùng cho mapbox_places.py nếu cần) ───
    mapbox_token: str | None = Field(
        default=None,
        description="Mapbox public/secret token (optional nếu dùng Google Places)",
    )

    # ── Internal Security ──────────────────────────────────────
    internal_api_key: str = Field(
        default="tripjoy-internal-key",
        description="Shared secret với Spring Boot backend (X-Internal-Api-Key header)",
    )

    # ── Server ────────────────────────────────────────────────
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    app_reload: bool = Field(default=False, description="Chỉ True trong development")
    log_level: str = Field(default="INFO")

    # ── Validators ────────────────────────────────────────────
    @field_validator("google_application_credentials", mode="before")
    @classmethod
    def validate_gcp_credentials_path(cls, v: str | None) -> str | None:
        """
        Validate rằng file credentials tồn tại nếu được cung cấp.
        Không cho phép relative path vì sẽ phụ thuộc vào cwd.
        """
        if v is None:
            return None

        path = Path(v)

        if not path.is_absolute():
            raise ValueError(
                f"GOOGLE_APPLICATION_CREDENTIALS phải là absolute path, nhận được: '{v}'. "
                f"Ví dụ đúng: '/app/secrets/service-account.json' hoặc "
                f"'/home/user/.config/gcloud/application_default_credentials.json'"
            )

        if not path.exists():
            raise ValueError(
                f"GOOGLE_APPLICATION_CREDENTIALS trỏ đến file không tồn tại: '{v}'. "
                f"Kiểm tra file đã được mount vào container chưa."
            )

        return str(path)

    @field_validator("log_level", mode="before")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        normalized = v.upper()
        if normalized not in allowed:
            raise ValueError(f"LOG_LEVEL phải là một trong {allowed}, nhận được: '{v}'")
        return normalized


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Singleton accessor cho Settings.
    Dùng @lru_cache để chỉ parse .env một lần duy nhất — thread-safe.

    Cách dùng trong các module khác:
        from travel_agent.config import get_settings
        settings = get_settings()
        api_key = settings.gg_api_key
    """
    return Settings()
