import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

import pytest
from app.agents.registry import AgentRegistry
from app.database import models as database_models  # noqa: F401
from app.database.base import Base
from app.database.session import engine as application_engine
from app.runtime.event_bus import EventBus
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# --------------------------------------------------
# Existing Runtime Fixtures
# --------------------------------------------------

@pytest.fixture
def event_bus():
    return EventBus()



@pytest.fixture
def agent_registry():
    return AgentRegistry()


@pytest.fixture(autouse=True)
def application_database_schema():
    """Keep application-level API tests isolated from production infrastructure."""

    Base.metadata.create_all(bind=application_engine)
    try:
        yield
    finally:
        Base.metadata.drop_all(bind=application_engine)



# --------------------------------------------------
# Database Test Configuration
# --------------------------------------------------

# SQLite in-memory database for tests
# Production uses AWS PostgreSQL

TEST_DATABASE_URL = (
    "sqlite:///:memory:"
)


engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={
        "check_same_thread": False
    },
    poolclass=StaticPool,
)



TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)



# --------------------------------------------------
# Database Session Fixture
# --------------------------------------------------

@pytest.fixture
def db_session():

    # Create tables before test

    Base.metadata.create_all(
        bind=engine
    )


    session = TestingSessionLocal()


    try:

        yield session


    finally:

        session.close()


        # Clean database after test

        Base.metadata.drop_all(
            bind=engine
        )
