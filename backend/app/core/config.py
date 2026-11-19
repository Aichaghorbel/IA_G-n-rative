import os
from typing import Any, List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuration globale de SmartCampus AI.
    Charge les variables d'environnement depuis le fichier .env
    avec valeurs par défaut robustes pour le développement et la production.
    """
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

    # ==============================================================================
    # Configuration PostgreSQL (Individuelle et URL complète)
    # ==============================================================================
    POSTGRES_USER: str = "smartcampus"
    POSTGRES_PASSWORD: str = "smartcampus_password"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "smartcampus"
    DATABASE_URL: str = "postgresql+psycopg2://smartcampus:smartcampus_password@localhost:5432/smartcampus"

    # ==============================================================================
    # Cache & Sessions (Redis)
    # ==============================================================================
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = False

    # ==============================================================================
    # Stockage Objets S3 (MinIO)
    # ==============================================================================
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin_secret"
    MINIO_ROOT_USER: str = "minioadmin"
    MINIO_ROOT_PASSWORD: str = "minioadmin_secret"
    MINIO_SECURE: bool = False
    MINIO_BUCKET_DOCS: str = "smartcampus-docs"
    MINIO_BUCKET_AUDIO: str = "smartcampus-audio"

    # ==============================================================================
    # Sécurité & Tokens JWT
    # ==============================================================================
    SECRET_KEY: str = "smartcampus-super-secret-key-change-me-in-production-2026!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15      # 15 minutes (Spécification section 6.4)
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7         # 7 jours
    VISITOR_SESSION_EXPIRE_DAYS: int = 30      # 30 jours sliding

    # ==============================================================================
    # CORS
    # ==============================================================================
    CORS_ORIGINS: List[str] = [
        "http://localhost:4200",
        "http://127.0.0.1:4200",
        "http://localhost:8000"
    ]

    # Limites de charge utile (octets)
    MAX_JSON_PAYLOAD_BYTES: int = 1 * 1024 * 1024       # 1 Mo
    MAX_AUDIO_PAYLOAD_BYTES: int = 10 * 1024 * 1024     # 10 Mo
    MAX_DOC_PAYLOAD_BYTES: int = 50 * 1024 * 1024       # 50 Mo
    MAX_IMAGE_PAYLOAD_BYTES: int = 5 * 1024 * 1024      # 5 Mo

    # ==============================================================================
    # IA, LLM & Embeddings
    # ==============================================================================
    LLM_PROVIDER: str = "openai_compatible"
    LLM_API_BASE: str = "http://localhost:11434/v1"
    LLM_API_KEY: str = "not-needed-for-local"
    LLM_MODEL: str = "qwen2.5-7b-instruct"
    WHISPER_MODEL: str = "base"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # ==============================================================================
    # Serveur SMTP (Mailpit pour tests locaux)
    # ==============================================================================
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

    @field_validator("DATABASE_URL", mode="before")
    def assemble_db_connection(cls, v: Any, info: Any) -> str:
        if isinstance(v, str) and v.strip() and not v.startswith("sqlite"):
            return v
        # Si DATABASE_URL n'est pas explicitement fournie, la déduire des paramètres POSTGRES
        data = info.data if hasattr(info, "data") else {}
        user = data.get("POSTGRES_USER", "smartcampus")
        password = data.get("POSTGRES_PASSWORD", "smartcampus_password")
        host = data.get("POSTGRES_HOST", "localhost")
        port = data.get("POSTGRES_PORT", 5432)
        db_name = data.get("POSTGRES_DB", "smartcampus")
        return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}"

    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        import json
        return json.loads(v)


settings = Settings()
