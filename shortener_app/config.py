from typing import ClassVar, TypeVar
from datetime import timedelta
from functools import lru_cache

from environs import Env
from snowflake import SnowflakeGenerator
from pydantic_settings import BaseSettings

from .security.auth.middleware.jwt.base.config import JWTConfig

env = Env()
env.read_env()

class Settings(BaseSettings):
    env_name: str = "Local"
    base_url: str = "sqlite+aiosqlite:///./shortener.db"
    db_url: str = "sqlite:///./shortener.db"
    async_db_url: str = "sqlite+aiosqlite:///./shortener.db"

    REDIS_HOST: str = env('REDIS_HOST')
    REDIS_PORT: int = env('REDIS_PORT')


    API_SECRET: str = env('API_SECRET')
    HASH_SALT: str = env('HASH_SALT')

    ALGORITHM: str = "HS256"
    JWT_SECRET: str = env('JWT_SECRET')
    ACCESS_TOKEN_TTL: int = env.int('ACCESS_TOKEN_TTL')
    REFRESH_TOKEN_TTL: int = env.int('REFRESH_TOKEN_TTL')
    jwt_config: JWTConfig = JWTConfig(
    secret=JWT_SECRET,
    algorithm=ALGORITHM,
    access_token_ttl=timedelta(seconds=ACCESS_TOKEN_TTL),
    refresh_token_ttl=timedelta(seconds=REFRESH_TOKEN_TTL),
    )
    snowflake_code: int = env.int("SNOWFLAKE_CODE")  


    DB_HOST: str = env("DB_HOST")
    DB_PORT: int = env("DB_PORT")
    DB_USER: str = env("DB_USER")
    DB_PASS: str = env("DB_PASS")
    DB_NAME: str = env("DB_NAME")

    @property
    def DATABASE_URL_asyncpg(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_USER}"
    
    @property
    def DATABASE_URL_psycopg(self):
        return f"postgresql+psycopg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_USER}"

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    print(f"Loading settings for: {settings.env_name}")
    return settings