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

    def _extract_content(self, content: str) -> str:
        """Extract meaningful content from transaction description.

        Primary pattern: "Ourxmas {content}" - extracts content after "Ourxmas "
        Example: "Ourxmas MyProject123" -> "MyProject123"

        Fallback patterns for legacy support:
            "MBVCB.12243110992.867260.khoi2.CT tu..." -> "khoi2"
            "BIDV;96247QTKN;beo san" -> "beo san"
        """
        import re

        # Primary pattern: Ourxmas {content}
        # Case-insensitive match for "Ourxmas" followed by the project name
        ourxmas_match = re.search(r"[Oo]urxmas\s+([A-Za-z0-9]+)", content)
        if ourxmas_match:
            return ourxmas_match.group(1).strip()

        # Fallback: Handle MBVCB format: MBVCB.{id}.{code}.{content}.CT tu...
        mbvcb_match = re.match(r"^MBVCB\.\d+\.\d+\.([^.]+)\.CT\s", content)
        if mbvcb_match:
            return mbvcb_match.group(1).strip()

        # Fallback: Another MBVCB variant without "CT tu"
        mbvcb_simple_match = re.match(r"^MBVCB\.\d+\.\d+\.([^.\s]+)", content)
        if mbvcb_simple_match:
            return mbvcb_simple_match.group(1).strip()

        # Fallback: Split by semicolon (e.g., "BIDV;96247QTKN;beo san")
        if ";" in content:
            return content.split(";")[-1].strip()

        # Fallback: Split by space and get last part
        if " " in content:
            return content.split()[-1].strip()

        return content.strip()

    def create_transaction(self, payload: SepayWebhookPayload) -> Transaction:
        """Create a new transaction from webhook payload.

        Returns:
            Transaction: newly created transaction
        """
        # Parse transaction date
        transaction_date = datetime.strptime(
            payload.transactionDate, "%Y-%m-%d %H:%M:%S"
        )

        # Extract content from transaction description
        parsed_content = self._extract_content(payload.content)

        transaction = Transaction(
            sepay_id=payload.id,
            gateway=payload.gateway,
            transaction_date=transaction_date,
            account_number=payload.accountNumber,
            content=parsed_content,
            transfer_type=payload.transferType,
            amount=payload.transferAmount,
            reference_code=payload.referenceCode,
            description=payload.description,
        )

        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

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
