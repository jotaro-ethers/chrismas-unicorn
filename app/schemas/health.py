from datetime import datetime
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str
    timestamp: datetime
    version: str


class ReadyResponse(BaseModel):
    """Readiness check response schema."""
    ready: bool
    database: str
    timestamp: datetime
