"""
config.py — Configuración centralizada del sistema.

Usa Pydantic Settings para cargar variables de entorno
con validación y valores por defecto seguros.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración del servidor FinEngine."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "FinEngine"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "dev-secret-change-in-production"

    # Database
    database_url: str = "sqlite+aiosqlite:///./finengine_dev.db"

    # JWT
    jwt_secret_key: str = "dev-jwt-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # Monte Carlo
    monte_carlo_default_iterations: int = 10_000

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.app_env == "production"


# Singleton
settings = Settings()
