"""
Application configuration — all settings read from environment variables.

Uses Pydantic Settings for validation and type coercion. No hardcoded
secrets anywhere in the codebase; every configurable value lives here.
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "MarutiSuzukiKnowledgeAssistant"
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_log_level: str = "INFO"

    # --- Database ---
    postgres_host: str = "db"
    postgres_port: int = 5432
    postgres_db: str = "mskai"
    postgres_user: str = "mskai_user"
    postgres_password: str = "CHANGE_ME_IN_PRODUCTION"

    database_url_override: Optional[str] = None
    database_url_sync_override: Optional[str] = None

    @property
    def database_url(self) -> str:
        """Async connection string."""
        if self.database_url_override:
            return self.database_url_override
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        """Sync connection string."""
        if self.database_url_sync_override:
            return self.database_url_sync_override
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


    # --- JWT / Auth ---
    jwt_secret_key: str = "CHANGE_ME_USE_OPENSSL_RAND_HEX_32"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # --- AI Provider ---
    ai_provider: str = "azure_openai"
    azure_openai_api_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_deployment_name: str = ""
    azure_openai_api_version: str = "2024-02-15-preview"
    copilot_studio_bot_id: str = ""
    copilot_studio_tenant_id: str = ""
    copilot_studio_token_endpoint: str = ""

    # --- RAG ---
    rag_confidence_threshold: float = 0.65
    rag_top_k: int = 10
    rag_rerank_top_n: int = 5
    rag_chunk_size: int = 512
    rag_chunk_overlap: int = 64

    # --- Embedding ---
    embedding_model_name: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    # --- Storage ---
    file_storage_path: str = "./storage/documents"
    vector_store_path: str = "./storage/vectors"

    # --- PII ---
    pii_scan_enabled: bool = True

    # --- Rate Limiting ---
    rate_limit_requests_per_minute: int = 60
    rate_limit_ai_calls_per_hour: int = 100

    # --- CORS ---
    cors_origins: str = "http://localhost:3000,http://localhost:8080"

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse CORS origins into a list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # --- Data Residency ---
    data_residency: str = "india"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
