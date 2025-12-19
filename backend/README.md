# FastAPI Supabase Backend

FastAPI backend with Supabase database integration for CRUD operations.

## Quick Start

### Prerequisites

- Python 3.11+
- Supabase project (create one at [supabase.com](https://supabase.com))

### Setup

1. **Clone and navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Install and setup**
   ```bash
   make install  # Creates venv and installs dependencies
   ```

   Or manually:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your Supabase credentials:
   - `SUPABASE_URL`: Your Supabase project URL
   - `SUPABASE_ANON_KEY`: Anon/public key from Supabase settings
   - `SUPABASE_SERVICE_KEY`: Service role key (keep secret!)

4. **Create user_sessions table in Supabase**
   Run the SQL script provided in `supabase_setup.sql` in your Supabase SQL editor.
   The table includes:
   - `id`: UUID primary key
   - `phone_number`: User's phone number
   - `session_link`: Optional session link
   - `session_images`: Array of image URLs
   - `payment_status`: One of 'pending', 'paid', 'failed', 'refunded'
   - Timestamps for created_at and updated_at

### Running the Server

Choose one of the following methods:

**Option 1: Using the startup script (Recommended)**
```bash
make start  # Linux/macOS
./scripts/start.sh  # Linux/macOS
scripts\start.bat  # Windows
```

**Option 2: Using the Python script**
```bash
python scripts/start_server.py
```

**Option 3: Manual command**
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn main_app.main:app --reload
```

**Option 4: Using the installed CLI**
```bash
source venv/bin/activate
fastapi-start
```

The server will be running at:
- Main app: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## API Endpoints

### User Sessions

- `GET /api/v1/user-sessions` - List all sessions (with pagination, optional payment status filter)
- `POST /api/v1/user-sessions` - Create a new session
- `GET /api/v1/user-sessions/{id}` - Get session by ID
- `GET /api/v1/user-sessions/phone/{phone_number}` - Get all sessions for a phone number
- `PUT /api/v1/user-sessions/{id}` - Update a session
- `DELETE /api/v1/user-sessions/{id}` - Delete a session
- `GET /api/v1/user-sessions/count/total` - Get total count (optional payment status filter)

### Other

- `GET /` - Welcome message
- `GET /health` - Health check

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black src tests
```

### Linting

```bash
ruff check src tests
```

### Type Checking

```bash
mypy src
```

## Example Requests

### Create a User Session

```bash
curl -X POST "http://localhost:8000/api/v1/user-sessions" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "session_link": "https://example.com/session/123",
    "session_images": [
      "https://example.com/image1.jpg",
      "https://example.com/image2.jpg"
    ],
    "payment_status": "pending"
  }'
```

### List User Sessions

```bash
curl "http://localhost:8000/api/v1/user-sessions?limit=10&offset=0"
curl "http://localhost:8000/api/v1/user-sessions?payment_status=paid"
```

### Get Sessions by Phone Number

```bash
curl "http://localhost:8000/api/v1/user-sessions/phone/+1234567890"
```

### Update User Session

```bash
curl -X PUT "http://localhost:8000/api/v1/user-sessions/{session_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "payment_status": "paid",
    "session_images": ["https://example.com/image3.jpg"]
  }'
```

## Project Structure

```
backend/
├── src/main_app/
│   ├── api/v1/endpoints/    # API routes
│   ├── core/               # Configuration and database
│   ├── models/             # Pydantic models
│   └── services/           # Business logic
├── tests/                  # Test suite
└── pyproject.toml          # Project configuration
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_ANON_KEY` | Supabase anon key | Yes |
| `SUPABASE_SERVICE_KEY` | Supabase service role key | Yes |
| `API_V1_STR` | API v1 prefix | No (default: /api/v1) |
| `DEBUG` | Debug mode | No (default: True) |

## Troubleshooting

### ModuleNotFoundError: No module named 'src'

**Issue**: Running `uvicorn src.main_app.main:app --reload` fails with module error.

**Solution**: The correct module path is `main_app.main:app` (without the `src.` prefix). Make sure to:

1. Install the package in editable mode:
   ```bash
   pip install -e .
   ```

2. Use the correct command:
   ```bash
   uvicorn main_app.main:app --reload
   ```

Or use the provided startup script which handles this automatically:
```bash
./scripts/start.sh
```

### Port already in use

**Issue**: Server fails with "Address already in use" error.

**Solution**: Kill the process or use a different port:
```bash
# Find and kill the process
lsof -ti:8000 | xargs kill

# Or use a different port
uvicorn main_app.main:app --reload --port 8001
```

### Missing environment variables

**Issue**: Server fails with validation errors for missing Supabase credentials.

**Solution**: Create and configure your `.env` file:
```bash
cp .env.example .env
# Edit .env with your actual Supabase credentials
```

### Virtual environment issues

**Issue**: Dependencies not found or Python version mismatch.

**Solution**: Recreate the virtual environment:
```bash
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -e .
```

## Development Commands

```bash
# Install with dev dependencies
make dev

# Run tests
make test

# Format code
make format

# Run linting
make lint

# Clean cache
make clean
```

## License

MIT