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
    base_url: str = "http://localhost:8000"
    db_url: str = "sqlite:///./shortener.db"
    async_db_url: str = "sqlite+aiosqlite:///./shortener.db"

    # SECRET_KEY: str = "your_secret_key"
    # ALGORITHM: str = "HS256"
    # ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    API_SECRET: str = env('API_SECRET')
    HASH_SALT: str = env('HASH_SALT')

    JWT_SECRET: str = env('JWT_SECRET')
    ACCESS_TOKEN_TTL: int = env.int('ACCESS_TOKEN_TTL')
    REFRESH_TOKEN_TTL: int = env.int('REFRESH_TOKEN_TTL')
    jwt_config: JWTConfig = JWTConfig(
    secret=JWT_SECRET,
    access_token_ttl=timedelta(seconds=ACCESS_TOKEN_TTL),
    refresh_token_ttl=timedelta(seconds=REFRESH_TOKEN_TTL),
    )
    snowflake_code: int = env.int("SNOWFLAKE_CODE")  


    # DB_HOST: str
    # DB_PORT: int
    # DB_USER: str
    # DB_PASS: str
    # DB_NAME: str

    # @property
    # def db_url(self):
    #     return "sqlite:///./shortener.db"

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