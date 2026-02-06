"""Configuration management using Pydantic Settings."""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = "FarmLokal API"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database
    database_url: str
    db_echo: bool = False
    
    # Redis
    redis_url: str
    redis_max_connections: int = 10
    
    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    
    # OAuth - Google
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str
    
    # External API
    external_api_url: str
    external_api_timeout: int = 5
    external_api_max_retries: int = 3
    
    # Rate Limiting
    rate_limit_per_minute: int = 100
    rate_limit_per_ip: int = 200
    
    # Cache
    cache_ttl_seconds: int = 300
    cache_enabled: bool = True
    
    # Circuit Breaker
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: int = 30
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
