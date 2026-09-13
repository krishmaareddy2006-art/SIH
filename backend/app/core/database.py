"""SQLAlchemy Database Configuration supporting SQLite and Neon Serverless PostgreSQL."""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

# 1. Normalize Postgres connection URL (Neon provides postgres://, SQLAlchemy requires postgresql://)
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# 2. Configure engine based on database dialect (SQLite vs Neon Serverless PostgreSQL)
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    engine = create_engine(
        db_url,
        connect_args=connect_args,
        echo=False,
    )
else:
    # Neon Serverless PostgreSQL connection pooling settings:
    # - pool_pre_ping=True: Prevents "server closed connection unexpectedly" when Neon compute auto-suspends.
    # - pool_recycle=300: Recycles stale connections every 5 minutes.
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency for providing transactional database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
