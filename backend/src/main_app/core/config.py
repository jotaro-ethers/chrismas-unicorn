from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings."""

    # Supabase Configuration
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str

    # FastAPI Configuration
    api_v1_str: str = "/api/v1"
    project_name: str = "FastAPI Supabase Backend"
    environment: str = "development"
    debug: bool = True

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS Configuration
    cors_origins: List[str] = [
        "http://localhost:3000",  # React
        "http://localhost:5173",  # Vite
        "http://localhost:8080",  # Vue
        "http://localhost:4200",  # Angular
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


settings = Settings()