"""
Database engine and session management.
Uses SQLite with SQLAlchemy for ORM.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Database file stored in project data directory
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
os.makedirs(DATA_DIR, exist_ok=True)

DATABASE_URL = f"sqlite:///{os.path.join(DATA_DIR, 'tutor.db')}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables if they don't exist."""
    from app.database.models import User, ChatHistory, QuizResult, MoodLog  # noqa: F401
    Base.metadata.create_all(bind=engine)
    _migrate_db()


def _migrate_db():
    """Safely add new columns to existing SQLite databases (idempotent)."""
    with engine.connect() as conn:
        # Add 'role' column to users if it doesn't exist yet
        try:
            conn.execute(
                __import__('sqlalchemy').text("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'student'")
            )
            conn.commit()
        except Exception:
            pass  # Column already exists — ignore
        # Add 'name' NOT NULL default if somehow missing
        try:
            conn.execute(
                __import__('sqlalchemy').text("ALTER TABLE users ADD COLUMN name TEXT NOT NULL DEFAULT 'Student'")
            )
            conn.commit()
        except Exception:
            pass  # Column already exists — ignore

