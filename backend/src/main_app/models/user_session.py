from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from enum import Enum


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class UserSessionBase(BaseModel):
    phone_number: str = Field(..., min_length=10, max_length=20)
    session_link: Optional[str] = Field(None, max_length=500)
    session_images: List[str] = Field(default_factory=list)
    payment_status: PaymentStatus = PaymentStatus.PENDING


class UserSessionCreate(UserSessionBase):
    pass


class UserSessionUpdate(BaseModel):
    phone_number: Optional[str] = Field(None, min_length=10, max_length=20)
    session_link: Optional[str] = Field(None, max_length=500)
    session_images: Optional[List[str]] = None
    payment_status: Optional[PaymentStatus] = None


class UserSessionInDB(UserSessionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class UserSession(UserSessionInDB):
    pass