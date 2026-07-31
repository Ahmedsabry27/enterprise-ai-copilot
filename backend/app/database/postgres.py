from __future__ import annotations

from sqlalchemy import create_engine

from sqlalchemy.orm import (
    sessionmaker,
    Session,
)

from typing import Generator


# ---------------------------------
# Database Configuration
# ---------------------------------

DATABASE_URL = (
    "postgresql://postgres:Copilot2026%23Postgres@enterprise-ai-copilot-db.cyl6ycsqsk33.us-east-1.rds.amazonaws.com:5432/enterprise_ai_copilot"
)


# ---------------------------------
# Engine
# ---------------------------------

engine = create_engine(
    DATABASE_URL,
    echo=False,
)



# ---------------------------------
# Session Factory
# ---------------------------------

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)



# ---------------------------------
# FastAPI Dependency
# ---------------------------------

def get_db() -> Generator[
    Session,
    None,
    None,
]:
    """
    Provide database session.
    """

    db = SessionLocal()

    try:

        yield db

    finally:

        db.close()