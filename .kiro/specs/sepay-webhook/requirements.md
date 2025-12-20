# Requirements Document

## Introduction

Tài liệu này mô tả các yêu cầu cho việc xây dựng API callback nhận webhook từ Sepay - cổng thanh toán tự động. Webhook sẽ nhận thông báo giao dịch từ Sepay và xử lý dữ liệu thanh toán.

## Glossary

- **Sepay**: Cổng thanh toán tự động, gửi webhook khi có giao dịch ngân hàng
- **Webhook**: HTTP callback được gọi khi có sự kiện xảy ra
- **Callback URL**: Endpoint nhận webhook từ Sepay
- **Transaction**: Giao dịch thanh toán từ ngân hàng
- **API Key**: Khóa xác thực để verify webhook từ Sepay

## Requirements

### Requirement 1

**User Story:** As a system, I want to receive webhook notifications from Sepay, so that I can process payment transactions automatically.

#### Acceptance Criteria

1. WHEN Sepay sends a webhook POST request THEN the Backend SHALL accept the request at the configured callback endpoint
2. WHEN a webhook is received THEN the Backend SHALL validate the request using the Sepay API key
3. WHEN the webhook payload is received THEN the Backend SHALL parse the transaction data according to Sepay's schema
4. WHEN serializing webhook response THEN the Backend SHALL encode the response using the defined schema

### Requirement 2

**User Story:** As a system, I want to validate incoming webhooks, so that I can ensure the requests are authentic from Sepay.

#### Acceptance Criteria

1. WHEN a webhook request lacks valid authorization THEN the Backend SHALL return a 401 Unauthorized response
2. WHEN a webhook request contains invalid payload THEN the Backend SHALL return a 400 Bad Request response
3. IF the API key in the request does not match the configured key THEN the Backend SHALL reject the request

### Requirement 3

**User Story:** As a system, I want to store transaction data, so that I can track payment history.

#### Acceptance Criteria

1. WHEN a valid webhook is received THEN the Backend SHALL store the transaction data in the database
2. WHEN storing transaction data THEN the Backend SHALL include transaction ID, amount, content, account number, and timestamp
3. WHEN a duplicate transaction is received THEN the Backend SHALL skip insertion and return success

### Requirement 4

**User Story:** As a developer, I want to query transaction history, so that I can verify payments.

#### Acceptance Criteria

1. WHEN the transactions endpoint is called THEN the Backend SHALL return a list of stored transactions
2. WHEN querying transactions THEN the Backend SHALL support filtering by date range and transaction content
3. WHEN a specific transaction is queried THEN the Backend SHALL return the transaction details by ID

