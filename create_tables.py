"""Script to create database tables."""
from app.database import engine
from app.models.base import Base
from app.models.transaction import Transaction  # Import to register model

if __name__ == "__main__":
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")
