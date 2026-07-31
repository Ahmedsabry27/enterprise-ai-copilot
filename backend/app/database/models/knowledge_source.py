from datetime import UTC, datetime
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base

class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)
    source_type: Mapped[str] = mapped_column(default="DOCUMENT")
    location: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
