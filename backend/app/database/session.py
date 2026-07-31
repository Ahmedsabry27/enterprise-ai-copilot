from __future__ import annotations

import os

from dotenv import load_dotenv

from sqlalchemy import create_engine

from sqlalchemy.orm import (
    sessionmaker,
    Session,
)


# --------------------------------------------------
# Load environment
# --------------------------------------------------

load_dotenv()


DATABASE_URL = os.getenv(
    "DATABASE_URL"
)


if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not configured"
    )


# --------------------------------------------------
# SQLAlchemy Engine
# --------------------------------------------------

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)



# --------------------------------------------------
# Session Factory
# --------------------------------------------------

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)



# --------------------------------------------------
# FastAPI Dependency
# --------------------------------------------------

def get_db():
    """
    Provide database session.

    Usage:

    db: Session = Depends(get_db)
    """

    db: Session = SessionLocal()

    try:

        yield db

    finally:

        db.close()