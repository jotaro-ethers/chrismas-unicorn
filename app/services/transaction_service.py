from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.transaction import Transaction
from app.schemas.webhook import SepayWebhookPayload


class TransactionService:
    """Service for transaction operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_transaction(self, payload: SepayWebhookPayload) -> tuple[Transaction, bool]:
        """Create a new transaction from webhook payload.
        
        Returns:
            tuple: (transaction, is_new) - transaction object and whether it was newly created
        """
        # Check if transaction already exists
        existing = self.get_transaction_by_sepay_id(payload.id)
        if existing:
            return existing, False
        
        # Parse transaction date
        transaction_date = datetime.strptime(
            payload.transactionDate, "%Y-%m-%d %H:%M:%S"
        )
        
        transaction = Transaction(
            sepay_id=payload.id,
            gateway=payload.gateway,
            transaction_date=transaction_date,
            account_number=payload.accountNumber,
            content=payload.content,
            transfer_type=payload.transferType,
            amount=payload.transferAmount,
            reference_code=payload.referenceCode,
            description=payload.description,
        )
        
        try:
            self.db.add(transaction)
            self.db.commit()
            self.db.refresh(transaction)
            return transaction, True
        except IntegrityError:
            self.db.rollback()
            # Race condition: another request created it
            existing = self.get_transaction_by_sepay_id(payload.id)
            return existing, False
    
    def get_transaction(self, transaction_id: int) -> Optional[Transaction]:
        """Get transaction by internal ID."""
        return self.db.query(Transaction).filter(
            Transaction.id == transaction_id
        ).first()
    
    def get_transaction_by_sepay_id(self, sepay_id: int) -> Optional[Transaction]:
        """Get transaction by Sepay ID."""
        return self.db.query(Transaction).filter(
            Transaction.sepay_id == sepay_id
        ).first()
    
    def list_transactions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        content: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Transaction], int]:
        """List transactions with optional filters.
        
        Returns:
            tuple: (transactions, total_count)
        """
        query = self.db.query(Transaction)
        
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)
        if content:
            query = query.filter(Transaction.content.ilike(f"%{content}%"))
        
        total = query.count()
        transactions = query.order_by(
            Transaction.transaction_date.desc()
        ).offset(skip).limit(limit).all()
        
        return transactions, total
