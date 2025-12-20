from typing import Optional
from pydantic import BaseModel


class SepayWebhookPayload(BaseModel):
    """Sepay webhook payload schema."""
    id: int
    gateway: str
    transactionDate: str
    accountNumber: str
    code: Optional[str] = None
    content: str
    transferType: str  # "in" or "out"
    transferAmount: int
    accumulated: int
    subAccount: Optional[str] = None
    referenceCode: str
    description: str


class WebhookResponse(BaseModel):
    """Webhook response schema."""
    success: bool
    message: str
