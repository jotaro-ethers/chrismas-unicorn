from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TransactionResponse(BaseModel):
    """Transaction response schema."""
    id: int
    sepay_id: int
    gateway: str
    transaction_date: datetime
    account_number: str
    content: str
    transfer_type: str
    amount: int
    reference_code: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    """Transaction list response schema."""
    success: bool = True
    data: list[TransactionResponse]
    total: int
