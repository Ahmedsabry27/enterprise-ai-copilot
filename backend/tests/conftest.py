import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base

from app.runtime.event_bus import EventBus
from app.agents.registry import AgentRegistry


# --------------------------------------------------
# Existing Runtime Fixtures
# --------------------------------------------------

@pytest.fixture
def event_bus():
    return EventBus()



@pytest.fixture
def agent_registry():
    return AgentRegistry()



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