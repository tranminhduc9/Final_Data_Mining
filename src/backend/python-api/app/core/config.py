from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TechPulse AI Service"
    app_env: str = "development"
    port: int = 8001
    postgres_connection_string: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=("../.env", "../.env.example", ".env", ".env.example"),
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
