from app.database.base import Base
from app.database.session import engine

# Import all models so SQLAlchemy registers them
from app.models.conversation import Conversation
from app.models.message import Message


def init_db():
    Base.metadata.create_all(bind=engine)