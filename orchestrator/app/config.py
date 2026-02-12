from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    google_places_api_key: str = ""
    resend_api_key: str = ""
    serpapi_key: str = ""
    database_url: str = "postgresql://harness:password@localhost:5432/harnessai"
    redis_url: str = "redis://localhost:6379"
    base_url: str = "http://localhost:3000"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
