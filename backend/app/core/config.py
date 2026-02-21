from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "HackEurope 2026 API"
    environment: Literal["development", "testing", "production"] = "development"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/hackeurope"
    secret_key: str = "super_insecure_default_key"
    debug: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
