# Design Document: Sepay Webhook Callback

## Overview

Thiết kế API callback nhận webhook từ Sepay để xử lý thông báo giao dịch thanh toán tự động. Hệ thống sẽ validate, parse và lưu trữ transaction data.

## Sepay Webhook Payload

Sepay gửi webhook với payload format:

```json
{
  "id": 93,
  "gateway": "MBBank",
  "transactionDate": "2024-07-26 02:42:16",
  "accountNumber": "0839993888",
  "code": null,
  "content": "chuyen tien mua hang",
  "transferType": "in",
  "transferAmount": 5000000,
  "accumulated": 5000000,
  "subAccount": null,
  "referenceCode": "FT24208483191809",
  "description": "chuyen tien mua hang"
}
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Sepay Webhook Flow                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Sepay Server                                                │
│       │                                                      │
│       ▼                                                      │
│  POST /api/v1/webhook/sepay                                  │
│       │                                                      │
│       ▼                                                      │
│  ┌─────────────────┐                                         │
│  │  Auth Middleware │ ──── Validate API Key                  │
│  └────────┬────────┘                                         │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────┐                                         │
│  │  Webhook Router  │ ──── Parse & Validate Payload          │
│  └────────┬────────┘                                         │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────┐                                         │
│  │ Transaction Svc  │ ──── Process & Store Transaction       │
│  └────────┬────────┘                                         │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────┐                                         │
│  │    Database      │ ──── Supabase PostgreSQL               │
│  └─────────────────┘                                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure (additions)

```
app/
├── routers/
│   ├── webhook.py          # Webhook callback endpoints
│   └── transactions.py     # Transaction query endpoints
├── models/
│   └── transaction.py      # Transaction SQLAlchemy model
├── schemas/
│   ├── webhook.py          # Sepay webhook schemas
│   └── transaction.py      # Transaction response schemas
├── services/
│   └── transaction_service.py  # Transaction business logic
└── dependencies/
    └── auth.py             # API key authentication
```

## Components and Interfaces

### 1. Webhook Router (routers/webhook.py)

```python
router = APIRouter(prefix="/api/v1/webhook", tags=["Webhook"])

# POST /api/v1/webhook/sepay
@router.post("/sepay")
async def sepay_callback(
    payload: SepayWebhookPayload,
    api_key: str = Depends(verify_sepay_api_key)
) -> WebhookResponse
```

### 2. Transaction Router (routers/transactions.py)

```python
router = APIRouter(prefix="/api/v1/transactions", tags=["Transactions"])

# GET /api/v1/transactions
@router.get("/")
async def list_transactions(
    start_date: Optional[datetime],
    end_date: Optional[datetime],
    content: Optional[str]
) -> List[TransactionResponse]

# GET /api/v1/transactions/{transaction_id}
@router.get("/{transaction_id}")
async def get_transaction(transaction_id: int) -> TransactionResponse
```

### 3. Schemas

```python
# Sepay Webhook Payload
class SepayWebhookPayload(BaseModel):
    id: int
    gateway: str
    transactionDate: str
    accountNumber: str
    code: Optional[str]
    content: str
    transferType: str  # "in" or "out"
    transferAmount: int
    accumulated: int
    subAccount: Optional[str]
    referenceCode: str
    description: str

# Webhook Response
class WebhookResponse(BaseModel):
    success: bool
    message: str

# Transaction Response
class TransactionResponse(BaseModel):
    id: int
    sepay_id: int
    gateway: str
    transaction_date: datetime
    account_number: str
    content: str
    transfer_type: str
    amount: int
    reference_code: str
    created_at: datetime
```

### 4. Transaction Model

```python
class Transaction(Base, TimestampMixin):
    __tablename__ = "transactions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    sepay_id: Mapped[int] = mapped_column(unique=True)  # Sepay transaction ID
    gateway: Mapped[str]
    transaction_date: Mapped[datetime]
    account_number: Mapped[str]
    content: Mapped[str]
    transfer_type: Mapped[str]
    amount: Mapped[int]
    reference_code: Mapped[str]
    description: Mapped[Optional[str]]
```

### 5. Authentication Dependency

```python
# dependencies/auth.py
async def verify_sepay_api_key(
    authorization: str = Header(..., alias="Authorization")
) -> str:
    """Verify Sepay API key from Authorization header."""
    settings = get_settings()
    if authorization != f"Apikey {settings.SEPAY_API_KEY}":
        raise HTTPException(status_code=401, detail="Invalid API key")
    return authorization
```

### 6. Transaction Service

```python
class TransactionService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_transaction(self, payload: SepayWebhookPayload) -> Transaction
    def get_transaction(self, transaction_id: int) -> Optional[Transaction]
    def get_transaction_by_sepay_id(self, sepay_id: int) -> Optional[Transaction]
    def list_transactions(
        self, 
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        content: Optional[str]
    ) -> List[Transaction]
```

## Configuration Updates

```python
# config.py additions
class Settings(BaseSettings):
    # ... existing settings
    SEPAY_API_KEY: str = ""  # API key for webhook authentication
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: API Key Validation
*For any* webhook request, if the API key does not match the configured SEPAY_API_KEY, the Backend should return a 401 Unauthorized response.
**Validates: Requirements 1.2, 2.1, 2.3**

### Property 2: Webhook Schema Round-Trip
*For any* valid SepayWebhookPayload, serializing to JSON and parsing back should produce an equivalent object.
**Validates: Requirements 1.3, 1.4**

### Property 3: Invalid Payload Rejection
*For any* webhook request with payload that does not conform to SepayWebhookPayload schema, the Backend should return a 400 or 422 error response.
**Validates: Requirements 2.2**

### Property 4: Transaction Storage Completeness
*For any* valid webhook received, the stored transaction should contain all required fields: sepay_id, gateway, transaction_date, account_number, content, transfer_type, amount, reference_code.
**Validates: Requirements 3.1, 3.2**

### Property 5: Idempotent Transaction Processing
*For any* duplicate webhook with the same sepay_id, the Backend should not create duplicate records and should return success.
**Validates: Requirements 3.3**

### Property 6: Transaction Query Filtering
*For any* query with date range or content filter, all returned transactions should match the specified filter criteria.
**Validates: Requirements 4.2, 4.3**

## Error Handling

| Scenario | Status Code | Response |
|----------|-------------|----------|
| Missing/Invalid API key | 401 | `{"success": false, "error": "Invalid API key"}` |
| Invalid payload | 422 | `{"success": false, "error": "Validation Error", "detail": [...]}` |
| Duplicate transaction | 200 | `{"success": true, "message": "Transaction already processed"}` |
| Database error | 500 | `{"success": false, "error": "Internal Server Error"}` |
| Transaction not found | 404 | `{"success": false, "error": "Transaction not found"}` |

## Testing Strategy

### Testing Framework
- **pytest**: Main testing framework
- **hypothesis**: Property-based testing

### Property-Based Tests

1. **API Key Validation Test**: Generate random API keys, verify 401 for mismatches
2. **Schema Round-Trip Test**: Generate valid payloads, serialize/deserialize, verify equality
3. **Idempotency Test**: Send same transaction twice, verify single record
4. **Filter Test**: Generate transactions with various dates/content, verify filter correctness

### Integration Tests
- Test full webhook flow with valid payload
- Test authentication rejection
- Test transaction query endpoints

