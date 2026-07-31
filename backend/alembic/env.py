from __future__ import annotations

from logging.config import fileConfig
from pathlib import Path
import os

from alembic import context

from dotenv import load_dotenv

from sqlalchemy import (
    engine_from_config,
    pool,
)


# --------------------------------------------------
# Load environment variables
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]

load_dotenv(
    BASE_DIR / ".env"
)


DATABASE_URL = os.getenv(
    "DATABASE_URL"
)


if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL not found in .env"
    )


# --------------------------------------------------
# Alembic Config
# --------------------------------------------------

config = context.config


config.set_main_option(
    "sqlalchemy.url",
    DATABASE_URL,
)


if config.config_file_name is not None:

    fileConfig(
        config.config_file_name
    )


# --------------------------------------------------
# Import SQLAlchemy Metadata
# --------------------------------------------------

from app.database.base import Base


# Import all database models
# Required so Alembic can detect tables

from app.database.models import (
    User,
    Workflow,
    Task,
    Agent,
    Action,
    AuditLog,
)


target_metadata = Base.metadata



# --------------------------------------------------
# Offline Migration
# --------------------------------------------------

def run_migrations_offline() -> None:

    context.configure(
        url=DATABASE_URL,

        target_metadata=target_metadata,

        literal_binds=True,

        compare_type=True,
    )


    with context.begin_transaction():

        context.run_migrations()



# --------------------------------------------------
# Online Migration
# --------------------------------------------------

def run_migrations_online() -> None:

    connectable = engine_from_config(

        config.get_section(
            config.config_ini_section
        ),

        prefix="sqlalchemy.",

        poolclass=pool.NullPool,

    )


    with connectable.connect() as connection:

        context.configure(

            connection=connection,

            target_metadata=target_metadata,

            compare_type=True,

        )


        with context.begin_transaction():

            context.run_migrations()



# --------------------------------------------------
# Entry Point
# --------------------------------------------------

if context.is_offline_mode():

    run_migrations_offline()

else:

    run_migrations_online()