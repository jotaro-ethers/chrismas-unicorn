from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.transaction import TransactionResponse, TransactionListResponse
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/api/v1/transactions", tags=["Transactions"])


@router.get("", response_model=TransactionListResponse)
async def list_transactions(
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    content: Optional[str] = Query(None, description="Filter by content (partial match)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    db: Session = Depends(get_db),
) -> TransactionListResponse:
    """List transactions with optional filters."""
    service = TransactionService(db)
    transactions, total = service.list_transactions(
        start_date=start_date,
        end_date=end_date,
        content=content,
        skip=skip,
        limit=limit,
    )

    return TransactionListResponse(
        success=True,
        data=[TransactionResponse.model_validate(t) for t in transactions],
        total=total,
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
) -> TransactionResponse:
    """Get a specific transaction by ID."""
    service = TransactionService(db)
    transaction = service.get_transaction(transaction_id)

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return TransactionResponse.model_validate(transaction)
