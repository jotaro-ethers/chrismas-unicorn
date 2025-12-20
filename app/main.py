from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.middleware.error_handler import (
    validation_exception_handler,
    http_exception_handler,
    generic_exception_handler,
)
from app.routers import health, webhook, transactions


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        debug=settings.DEBUG,
    )
    
    # Register CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register exception handlers
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    # Register routers
    app.include_router(health.router)
    app.include_router(webhook.router)
    app.include_router(transactions.router)
    
    return app


app = create_app()


@app.get("/")
async def root():
    """Root endpoint - Hello World."""
    return {"message": "Hello World"}
