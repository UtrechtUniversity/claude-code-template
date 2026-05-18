from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://app:app@localhost:5432/app"


@lru_cache
def get_settings() -> Settings:
    return Settings()
