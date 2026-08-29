"""
Application settings configuration using Pydantic BaseSettings.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI-Powered Ticket Management System"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "super-secret-key-change-in-production-ticket-system-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day for local dev convenience
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./ticket_system.db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "ticket_system"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    # AI & Model Configuration
    DEFAULT_MODEL: str = "gpt-oss:120b-cloud"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_PROVIDER: str = "ollama"  # ollama | mock | openai
    LLM_TIMEOUT: float = 60.0
    OPENAI_API_KEY: str = "local"
    LOG_COSTS: bool = True

    # Storage
    UPLOAD_DIR: str = "./uploads"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()

