import os
from typing import Any, List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    APP_NAME: str = "SmartCampus AI"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str = "sqlite:///./smartcampus.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = False

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin_secret"
    MINIO_SECURE: bool = False
    MINIO_BUCKET_DOCS: str = "smartcampus-docs"
    MINIO_BUCKET_AUDIO: str = "smartcampus-audio"

    # Security & Tokens
    SECRET_KEY: str = "smartcampus-super-secret-key-change-me-in-production-2026!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15      # 15 minutes as per spec section 6.4
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7         # 7 days as per spec section 6.4
    VISITOR_SESSION_EXPIRE_DAYS: int = 30      # 30 days sliding as per spec section 6.4

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:4200",
        "http://127.0.0.1:4200",
        "http://localhost:8000"
    ]

    # Payload limits (bytes) - Section 4.2
    MAX_JSON_PAYLOAD_BYTES: int = 1 * 1024 * 1024       # 1 Mo
    MAX_AUDIO_PAYLOAD_BYTES: int = 10 * 1024 * 1024     # 10 Mo
    MAX_DOC_PAYLOAD_BYTES: int = 50 * 1024 * 1024       # 50 Mo
    MAX_IMAGE_PAYLOAD_BYTES: int = 5 * 1024 * 1024      # 5 Mo

    # AI & RAG
    LLM_PROVIDER: str = "openai_compatible"
    LLM_API_BASE: str = "http://localhost:11434/v1"
    LLM_API_KEY: str = "not-needed-for-local"
    LLM_MODEL: str = "qwen2.5-7b-instruct"
    WHISPER_MODEL: str = "base"

    # SMTP Mailpit
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_EMAIL: str = "contact@smartcampus.tn"
    EMAILS_FROM_NAME: str = "SmartCampus AI"

    @field_validator("DEBUG", mode="before")
    def assemble_debug(cls, v: Any) -> bool:
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            val = v.strip().lower()
            if val in ("true", "1", "yes", "debug", "dev", "development"):
                return True
            if val in ("false", "0", "no", "release", "prod", "production", "off"):
                return False
        return False
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        import json
        return json.loads(v)


settings = Settings()
