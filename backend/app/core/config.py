from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional

class Settings(BaseSettings):
    SUPABASE_URL: str = "http://localhost:8000"
    SUPABASE_KEY: str = "your_supabase_anon_key"
    SUPABASE_JWT_SECRET: str = "your_supabase_jwt_secret"
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"
    SUPABASE_STORAGE_URL: str = "http://localhost:8000/storage/v1/object/public"
    ENCRYPTION_KEY: str = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USER: str = "user"
    SMTP_PASSWORD: str = "password"
    SMTP_FROM_EMAIL: str = "noreply@maars.gov.in"
    EMAIL_DRY_RUN: bool = True
    CORS_ORIGINS: List[str] = ["*"]

    # OCR Engine Configuration
    OCR_ENGINE: str = "winocr"  # "winocr" | "mock" | "paddleocr"
    OCR_LANGS: str = "en,hi"
    PADDLE_MODEL_DIR: Optional[str] = None
    PADDLE_ENABLE_MKLDNN: bool = False
    OCR_USE_GPU: bool = False
    OCR_MIN_CONFIDENCE: float = 0.70
    OCR_MAX_IMAGE_SIDE: int = 1920
    OCR_IOU_THRESHOLD: float = 0.40
    UPLOAD_DIR: str = "uploads"
    # Celery & Worker Configuration
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    ASYNC_OCR_ENABLED: bool = False  # If true, /upload delegates OCR to worker


    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

