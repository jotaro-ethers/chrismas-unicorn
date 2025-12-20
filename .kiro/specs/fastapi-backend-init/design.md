# Design Document: FastAPI Backend Initialization

## Overview

Thiết kế này mô tả kiến trúc và cấu trúc cho một FastAPI backend project với các thành phần cơ bản bao gồm routing, validation, database connection, error handling, và CORS configuration.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Application                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Middleware │  │    CORS     │  │  Exception Handler  │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                         Routers                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Health    │  │    API v1   │  │      Other...       │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                        Services                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              Business Logic Layer                        ││
│  └─────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────┤
│                       Repositories                           │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              Data Access Layer (SQLAlchemy)              ││
│  └─────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────┤
│                        Database                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                   Supabase (PostgreSQL)                  ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
app/
├── __init__.py
├── main.py                 # Application entry point
├── config.py               # Configuration management
├── database.py             # Database connection setup (SQLAlchemy + Supabase)
├── supabase_client.py      # Supabase client initialization
├── routers/
│   ├── __init__.py
│   └── health.py           # Health check endpoints
├── models/
│   ├── __init__.py
│   └── base.py             # SQLAlchemy base model
├── schemas/
│   ├── __init__.py
│   ├── base.py             # Base response schemas
│   └── health.py           # Health check schemas
├── services/
│   └── __init__.py
├── middleware/
│   ├── __init__.py
│   └── error_handler.py    # Global error handling
└── utils/
    └── __init__.py
tests/
├── __init__.py
├── conftest.py             # Pytest fixtures
└── test_health.py          # Health endpoint tests
requirements.txt
.env.example
```

## Components and Interfaces

### 1. Main Application (main.py)

```python
# Interface
class Application:
    app: FastAPI
    
    def create_app() -> FastAPI
    def register_routers(app: FastAPI) -> None
    def register_middleware(app: FastAPI) -> None
    def register_exception_handlers(app: FastAPI) -> None
```

### 2. Configuration (config.py)

```python
# Interface
class Settings(BaseSettings):
    APP_NAME: str
    DEBUG: bool
    
    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_DB_URL: str  # PostgreSQL connection string
    
    ALLOWED_ORIGINS: list[str]
    
    class Config:
        env_file = ".env"
```

### 3. Database (database.py)

```python
# Interface using Supabase PostgreSQL
class Database:
    engine: Engine  # SQLAlchemy engine connected to Supabase PostgreSQL
    SessionLocal: sessionmaker
    supabase_client: Client  # Supabase Python client for additional features
    
    def get_db() -> Generator[Session, None, None]
    def get_supabase() -> Client
    def create_tables() -> None
```

### 4. Supabase Client (supabase_client.py)

```python
# Interface for Supabase-specific operations
from supabase import create_client, Client

class SupabaseClient:
    client: Client
    
    def __init__(url: str, key: str) -> None
    def get_client() -> Client
```

### 4. Router Interface

```python
# Interface for all routers
router: APIRouter

# Health Router
GET /health -> HealthResponse
GET /health/ready -> ReadyResponse
```

### 5. Schema Interfaces

```python
# Base Response
class BaseResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any]

# Error Response
class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[Any]

# Health Response
class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
```

### 6. Error Handler Interface

```python
# Interface
class ErrorHandler:
    def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse
    def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse
    def handle_generic_exception(request: Request, exc: Exception) -> JSONResponse
```

## Data Models

### Base Model

```python
class BaseModel(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Configuration Loading Consistency
*For any* environment variable defined in the Settings class, loading the configuration should correctly retrieve the value from the environment.
**Validates: Requirements 1.2**

### Property 2: Request Routing Correctness
*For any* valid URL path registered with a router, the request should be routed to the correct handler function.
**Validates: Requirements 2.1**

### Property 3: Pydantic Schema Round-Trip
*For any* valid Pydantic model instance, serializing to JSON and then parsing back should produce an equivalent object.
**Validates: Requirements 3.3, 3.4**

### Property 4: Validation Error Consistency
*For any* request with invalid data according to the Pydantic schema, the Backend should return a 422 status with structured error details.
**Validates: Requirements 3.1, 5.2**

### Property 5: CORS Header Inclusion
*For any* cross-origin request from an allowed origin, the response should include appropriate CORS headers (Access-Control-Allow-Origin, Access-Control-Allow-Methods, Access-Control-Allow-Headers).
**Validates: Requirements 4.1, 4.2, 4.3**

### Property 6: Error Response Structure
*For any* exception (HTTP exception or unhandled exception), the response should follow the ErrorResponse schema with appropriate status code.
**Validates: Requirements 5.1, 5.3**

### Property 7: OpenAPI Schema Completeness
*For any* endpoint defined with a router, the endpoint should appear in the auto-generated OpenAPI schema at /openapi.json.
**Validates: Requirements 7.3**

## Error Handling

### Error Response Format

Tất cả error responses sẽ tuân theo format:

```json
{
    "success": false,
    "error": "Error type description",
    "detail": {
        "field": "error message"
    }
}
```

### HTTP Status Codes

| Status Code | Usage |
|-------------|-------|
| 200 | Successful request |
| 201 | Resource created |
| 400 | Bad request |
| 404 | Resource not found |
| 422 | Validation error |
| 500 | Internal server error |

### Exception Handlers

1. **RequestValidationError**: Return 422 with field-level errors
2. **HTTPException**: Return the specified status code with message
3. **Generic Exception**: Return 500 with generic error message (hide details in production)

## Testing Strategy

### Testing Framework
- **pytest**: Main testing framework
- **pytest-asyncio**: Async test support
- **httpx**: Async HTTP client for testing FastAPI
- **hypothesis**: Property-based testing library

### Unit Tests
- Test configuration loading
- Test schema validation
- Test error handlers
- Test individual router endpoints

### Property-Based Tests
Sử dụng **Hypothesis** library cho property-based testing:

1. **Schema Round-Trip Test**: Generate random valid data, serialize, deserialize, verify equality
2. **Validation Error Test**: Generate invalid data, verify 422 response format
3. **CORS Test**: Generate requests with various origins, verify header behavior
4. **Error Response Test**: Generate various exceptions, verify response structure

### Integration Tests
- Test full request/response cycle
- Test database connection lifecycle
- Test middleware chain
- Test Supabase client connection

### Test Configuration
- Minimum 100 iterations for property-based tests
- Use TestClient for synchronous endpoint tests
- Use AsyncClient for async endpoint tests

## Dependencies

```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
sqlalchemy>=2.0.0
supabase>=2.0.0
python-dotenv>=1.0.0
httpx>=0.26.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
hypothesis>=6.0.0
```
