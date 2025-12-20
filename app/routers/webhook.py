from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import verify_sepay_api_key
from app.schemas.webhook import SepayWebhookPayload, WebhookResponse
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/api/v1/webhook", tags=["Webhook"])


@router.post("/sepay", response_model=WebhookResponse)
async def sepay_callback(
    payload: SepayWebhookPayload,
    _: str = Depends(verify_sepay_api_key),
    db: Session = Depends(get_db),
) -> WebhookResponse:
    """Receive webhook callback from Sepay.
    
    This endpoint receives transaction notifications from Sepay
    and stores them in the database.
    """
    service = TransactionService(db)
    transaction, is_new = service.create_transaction(payload)
    
    if is_new:
        return WebhookResponse(
            success=True,
            message=f"Transaction {payload.id} processed successfully"
        )
    else:
        return WebhookResponse(
            success=True,
            message=f"Transaction {payload.id} already processed"
        )
