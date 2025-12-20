from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Transaction(Base, TimestampMixin):
    """Transaction model for storing Sepay webhook data."""
    __tablename__ = "transactions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    sepay_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    gateway: Mapped[str] = mapped_column(String(50))
    transaction_date: Mapped[datetime] = mapped_column(DateTime)
    account_number: Mapped[str] = mapped_column(String(50))
    content: Mapped[str] = mapped_column(String(500))
    transfer_type: Mapped[str] = mapped_column(String(10))  # "in" or "out"
    amount: Mapped[int] = mapped_column(Integer)
    reference_code: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
