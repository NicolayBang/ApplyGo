"""Application settings for the ApplyPilot scaffold."""

from functools import lru_cache
from typing import Iterable

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed settings used by the initial scaffold."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ApplyPilot"
    app_env: str = "development"
    debug: bool = False
    database_url: str = "postgresql+psycopg://applypilot:applypilot@localhost:5432/applypilot"
    redis_url: str = "redis://localhost:6379/0"
    cors_allowed_origins: str = ",".join(
        [
            "http://localhost:3000",
            "http://localhost:4173",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:4173",
            "http://127.0.0.1:5173",
        ]
    )

    def allowed_cors_origins(
        self,
        *,
        codespace_name: str = "",
        codespaces_domain: str = "app.github.dev",
    ) -> list[str]:
        """Build explicit allowed origins for local dev and optional Codespaces use."""

        configured_origins = [
            origin.strip()
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]
        codespaces_origins = []

        if codespace_name:
            codespaces_origins = [
                f"https://{codespace_name}-4173.{codespaces_domain}",
                f"https://{codespace_name}-3000.{codespaces_domain}",
                f"https://{codespace_name}-5173.{codespaces_domain}",
            ]

        return _dedupe(codespaces_origins + configured_origins)


def _dedupe(origins: Iterable[str]) -> list[str]:
    """Preserve order while removing repeated origin entries."""

    seen: set[str] = set()
    unique: list[str] = []
    for origin in origins:
        if origin not in seen:
            seen.add(origin)
            unique.append(origin)
    return unique


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()
