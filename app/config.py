"""
Configuration management using Pydantic Settings
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Google AI Configuration
    google_api_key: str
    gemini_model: str = "gemini-2.0-flash"

    # Logging Configuration
    log_level: str = "DEBUG"
    log_file: str = "logs/app.log"

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance

    Returns:
        Settings: Application settings
    """
    return Settings()


def clear_settings_cache():
    """Clear the settings cache to reload from .env"""
    get_settings.cache_clear()
