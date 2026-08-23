import os
from pathlib import Path

# Explicitly load .env into os.environ for google-cloud SDKs
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, _, value = line.partition("=")
                # Only set if not already in environment
                if key.strip() not in os.environ:
                    os.environ[key.strip()] = value.strip().strip("'\"")

try:
    # pyrefly: ignore [missing-import]
    from pydantic_settings import BaseSettings
except ImportError:
    try:
        from pydantic import BaseSettings  # type: ignore
    except ImportError:
        class BaseSettings:  # type: ignore
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

class Settings(BaseSettings):
    PROJECT_NAME: str = "KisanNet Backend API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Environment: 'production' (default) or 'development'
    # In development mode, auth dependencies allow a fallback dev identity with an explicit warning.
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")

    # Public base URL for Twilio webhooks (must be reachable by Twilio servers).
    # For local dev: use an ngrok HTTPS URL (e.g. https://abc123.ngrok.io).
    # For production: your deployed domain (e.g. https://api.kisannet.in).
    PUBLIC_BASE_URL: str = os.getenv("PUBLIC_BASE_URL", "")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/kisannet")

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Google Cloud & AI Settings
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-004")
    EMBEDDING_DIMENSION: int = 768
    
    # Pillar 3 Anti-Spam & Retries
    MAX_FEEDBACK_RETRIES: int = 3
    
    # Twilio Voice & SMS Settings (Pillars 1, 3, 4)
    # These MUST be set in .env for real calls. No hardcoded defaults.
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    # TWILIO_NUMBER must be your purchased Twilio phone number (e.g. +14155551234)
    TWILIO_NUMBER: str = os.getenv("TWILIO_NUMBER", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
