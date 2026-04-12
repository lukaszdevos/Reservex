"""Application settings loaded from environment variables / .env file.

Layer: infrastructure
All configuration values read via pydantic-settings — never hardcoded.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = (
        "postgresql+asyncpg://reservex:reservex@localhost:5432/reservex"
    )
    redis_url: str = "redis://localhost:6379"
    stripe_secret_key: str = "sk_test_placeholder"
    environment: str = "development"
    log_level: str = "INFO"
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    service_name: str = "reservex"
    reservation_expiry_interval_seconds: float = 1.0
    reservation_expiry_batch_size: int = 100

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings: Settings = Settings()
