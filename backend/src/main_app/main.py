from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from .core.config import settings
from .api.v1.endpoints import user_sessions

app = FastAPI(
    title=settings.project_name,
    description="FastAPI backend with Supabase integration",
    version="0.1.0",
    openapi_url=f"{settings.api_v1_str}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=600,
)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.project_name}",
        "environment": settings.environment,
        "docs": "/docs",
        "version": "0.1.0",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": settings.project_name}

# Include API routers
app.include_router(user_sessions.router, prefix=settings.api_v1_str)


def main():
    """Main function to run the uvicorn server."""
    uvicorn.run(
        "main_app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning",
    )


if __name__ == "__main__":
    main()