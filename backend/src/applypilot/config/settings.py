"""Application settings for the ApplyPilot scaffold."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed settings used by the initial scaffold."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ApplyPilot"
    app_env: str = "development"
    debug: bool = True
    database_url: str = "postgresql+psycopg://applypilot:applypilot@localhost:5432/applypilot"
    redis_url: str = "redis://localhost:6379/0"


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()
