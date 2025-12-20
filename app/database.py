from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.config import get_settings


settings = get_settings()

engine = create_engine(
    settings.SUPABASE_DB_URL,
    pool_pre_ping=True,
) if settings.SUPABASE_DB_URL else None

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
) if engine else None


def get_db() -> Generator[Session, None, None]:
    """Get database session dependency."""
    if SessionLocal is None:
        raise RuntimeError("Database not configured")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
