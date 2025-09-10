from pydantic_settings import BaseSettings
from pydantic import RedisDsn, Field, field_validator
from typing import Literal
from functools import lru_cache

class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = "Top Divers Hurghada  website server"
    APP_DESCRIPTION: str = "Top Divers Hurghada  website server"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True
    PORT: int = 8000
    
    # JWT Settings
    JWT_SECRET_KEY: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = "HS256"
    JWT_USER_ACCESS_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ADMIN_ACCESS_TOKEN_EXPIRE_DAYS: int = 30
    
    # Database Settings
    DB_ENGINE: str = "postgresql"
    DB_NAME: str
    DB_HOST: str
    DB_PORT: int = 5432   # ✅ الافتراضي
    DB_USERNAME: str
    DB_PASSWORD: str
    DB_REDIS_URI: RedisDsn
    
    # Payment Gateway
    EASYKASH_PRIVATE_KEY: str
    EASYKASH_SECRET_KEY: str
    
    # Admin Account
    ADMIN_NAME: str
    ADMIN_EMAIL: str
    ADMIN_USERNAME: str
    ADMIN_PASSWORD: str
    ADMIN_LEVEL: int
    
    # Construct database URL from components
    @property
    def DATABASE_URL(self) -> str:
        return f"{self.DB_ENGINE}+psycopg2://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # Validate that debug is False in production
    @field_validator("DEBUG", mode="before")
    @classmethod
    def validate_debug_in_production(cls, v, values):
        if values.data.get("ENVIRONMENT") == "production" and v:
            raise ValueError("DEBUG should be False in production")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
