from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from supabase import Client

from ....models.user_session import (
    UserSession, UserSessionCreate, UserSessionUpdate, PaymentStatus
)
from ....services.user_session_service import UserSessionService
from ....core.database import get_supabase_service_client

router = APIRouter(prefix="/user-sessions", tags=["user_sessions"])


def get_user_session_service(db: Client = Depends(get_supabase_service_client)) -> UserSessionService:
    return UserSessionService(db)


@router.post("/", response_model=UserSession, status_code=201)
async def create_user_session(
    session_data: UserSessionCreate,
    service: UserSessionService = Depends(get_user_session_service)
):
    """Create a new user session."""
    try:
        return await service.create(session_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[UserSession])
async def get_user_sessions(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    payment_status: Optional[PaymentStatus] = Query(None),
    service: UserSessionService = Depends(get_user_session_service)
):
    """Get all user sessions with optional payment status filter."""
    return await service.get_all(limit=limit, offset=offset, payment_status=payment_status)


@router.get("/{session_id}", response_model=UserSession)
async def get_user_session(
    session_id: str,
    service: UserSessionService = Depends(get_user_session_service)
):
    """Get a user session by ID."""
    session = await service.get_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="User session not found")
    return session


@router.get("/phone/{phone_number}", response_model=List[UserSession])
async def get_user_sessions_by_phone(
    phone_number: str,
    service: UserSessionService = Depends(get_user_session_service)
):
    """Get all sessions for a specific phone number."""
    return await service.get_by_phone(phone_number)


@router.put("/{session_id}", response_model=UserSession)
async def update_user_session(
    session_id: str,
    update_data: UserSessionUpdate,
    service: UserSessionService = Depends(get_user_session_service)
):
    """Update a user session."""
    session = await service.update(session_id, update_data)
    if not session:
        raise HTTPException(status_code=404, detail="User session not found")
    return session


@router.delete("/{session_id}", status_code=204)
async def delete_user_session(
    session_id: str,
    service: UserSessionService = Depends(get_user_session_service)
):
    """Delete a user session."""
    success = await service.delete(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="User session not found")


@router.get("/count/total")
async def get_user_sessions_count(
    payment_status: Optional[PaymentStatus] = Query(None),
    service: UserSessionService = Depends(get_user_session_service)
):
    """Get total count of user sessions, optionally filtered by payment status."""
    count = await service.count(payment_status=payment_status)
    return {"total": count}