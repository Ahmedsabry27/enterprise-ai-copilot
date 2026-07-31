from app.database.base import Base
from app.database.session import engine

# Import all models so SQLAlchemy registers them
from app.models.conversation import Conversation
from app.models.message import Message
from app.database.base import Base

from app.database.postgres import (
    engine,
    SessionLocal,
    get_db,
)


def init_db():
    Base.metadata.create_all(bind=engine)

__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
]