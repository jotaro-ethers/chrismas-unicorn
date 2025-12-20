# Implementation Plan

- [x] 1. Update configuration and dependencies
  - [x] 1.1 Add SEPAY_API_KEY to config.py and .env.example
    - Add SEPAY_API_KEY field to Settings class
    - Update .env.example with SEPAY_API_KEY placeholder
    - _Requirements: 1.2, 2.1_

- [-] 2. Create schemas for webhook and transactions
  - [x] 2.1 Create schemas/webhook.py with SepayWebhookPayload and WebhookResponse
    - Define all fields from Sepay webhook payload
    - Define WebhookResponse with success and message
    - _Requirements: 1.3, 1.4_
  - [x] 2.2 Create schemas/transaction.py with TransactionResponse
    - Define response schema for transaction queries
    - _Requirements: 4.1, 4.3_
  - [ ] 2.3 Write property test for webhook schema round-trip
    - **Property 2: Webhook Schema Round-Trip**
    - **Validates: Requirements 1.3, 1.4**

- [x] 3. Create Transaction model
  - [x] 3.1 Create models/transaction.py with Transaction model
    - Define all fields: sepay_id, gateway, transaction_date, account_number, content, transfer_type, amount, reference_code
    - Add unique constraint on sepay_id for idempotency
    - _Requirements: 3.1, 3.2, 3.3_

- [-] 4. Create authentication dependency
  - [x] 4.1 Create dependencies/auth.py with verify_sepay_api_key
    - Extract API key from Authorization header
    - Compare with configured SEPAY_API_KEY
    - Raise 401 if mismatch
    - _Requirements: 1.2, 2.1, 2.3_
  - [ ] 4.2 Write property test for API key validation
    - **Property 1: API Key Validation**
    - **Validates: Requirements 1.2, 2.1, 2.3**

- [-] 5. Create Transaction service
  - [x] 5.1 Create services/transaction_service.py
    - Implement create_transaction with duplicate check
    - Implement get_transaction and list_transactions with filters
    - _Requirements: 3.1, 3.2, 3.3, 4.1, 4.2, 4.3_
  - [ ] 5.2 Write property test for idempotent transaction processing
    - **Property 5: Idempotent Transaction Processing**
    - **Validates: Requirements 3.3**

- [-] 6. Create webhook router
  - [x] 6.1 Create routers/webhook.py with POST /api/v1/webhook/sepay
    - Accept SepayWebhookPayload
    - Use verify_sepay_api_key dependency
    - Call transaction service to store
    - Return WebhookResponse
    - _Requirements: 1.1, 1.2, 1.3, 3.1_
  - [ ] 6.2 Write property test for invalid payload rejection
    - **Property 3: Invalid Payload Rejection**
    - **Validates: Requirements 2.2**

- [-] 7. Create transactions router
  - [x] 7.1 Create routers/transactions.py with query endpoints
    - GET /api/v1/transactions with date and content filters
    - GET /api/v1/transactions/{transaction_id}
    - _Requirements: 4.1, 4.2, 4.3_
  - [ ] 7.2 Write property test for transaction query filtering
    - **Property 6: Transaction Query Filtering**
    - **Validates: Requirements 4.2, 4.3**

- [x] 8. Register routers in main.py
  - [x] 8.1 Update main.py to include webhook and transactions routers
    - Import and register webhook router
    - Import and register transactions router
    - _Requirements: 1.1, 4.1_

- [ ] 9. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Create integration tests
  - [ ] 10.1 Create tests/test_webhook.py
    - Test valid webhook creates transaction
    - Test invalid API key returns 401
    - Test duplicate webhook is idempotent
    - _Requirements: 1.1, 1.2, 2.1, 3.3_
  - [ ] 10.2 Create tests/test_transactions.py
    - Test list transactions endpoint
    - Test get transaction by ID
    - Test filtering by date and content
    - _Requirements: 4.1, 4.2, 4.3_

- [ ] 11. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

