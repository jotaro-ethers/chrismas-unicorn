from datetime import datetime
from fastapi import APIRouter

from app.config import get_settings
from app.schemas.health import HealthResponse, ReadyResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.VERSION
    )


@router.get("/ready", response_model=ReadyResponse)
async def readiness_check() -> ReadyResponse:
    """Readiness check endpoint."""
    # TODO: Add actual database connectivity check
    return ReadyResponse(
        ready=True,
        database="connected",
        timestamp=datetime.utcnow()
    )
