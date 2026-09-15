"""
Database connection setup.

Uses SQLAlchemy's declarative ORM against a PostgreSQL database. The
connection string is read from the DATABASE_URL environment variable so the
same code works locally (docker-compose) and in any cloud deployment.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://binduparakh:binduparakh@localhost:5432/binduparakh",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
