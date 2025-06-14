from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    GOOGLE_API_KEY: str = Field(..., env="GOOGLE_API_KEY")
    SERPAPI_API_KEY: str = Field(..., env="SERPAPI_API_KEY")
    MONGODB_URL: str = Field(..., env="MONGODB_URL")
    DATABASE_NAME: str = Field(..., env="DATABASE_NAME")
    STRIPE_API_KEY: str = Field(..., env="STRIPE_API_KEY")
    STRIPE_PRICE_ID: str = Field(..., env="STRIPE_PRICE_ID")
    GEMINI_MODEL: str = Field("gemini-2.5-flash-preview-04-17", env="GEMINI_MODEL")
    # Add any other global settings here
    ENV: Optional[str] = Field("dev", env="ENV")
    DEBUG: bool = Field(False, env="DEBUG")
    # Example: CORS origins
    CORS_ORIGINS: Optional[str] = Field("*", env="CORS_ORIGINS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
