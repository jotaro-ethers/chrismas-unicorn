from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    APP_NAME: str = "FastAPI Backend"
    DEBUG: bool = False
    VERSION: str = "0.1.0"

    # Supabase Configuration
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_DB_URL: str = ""

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    # Sepay Configuration
    SEPAY_API_KEY: str = ""

    # If you want typed access to AWS/S3 settings inside Settings, you can
    # uncomment/add them here (optional):
    # AWS_ACCESS_KEY_ID: str | None = None
    # AWS_SECRET_ACCESS_KEY: str | None = None
    # S3_BUCKET_NAME: str | None = None
    # S3_PUBLIC_URL: str | None = None
    # AWS_REGION: str = "us-east-1"

    # pydantic v2 / pydantic-settings configuration
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        # Ignore unknown/extra environment variables instead of forbidding them.
        # This prevents ValidationError when .env contains keys not declared above.
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
