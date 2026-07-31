from datetime import datetime

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.database.base import Base



class AuditLog(Base):

    __tablename__ = "audit_logs"


    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )


    tenant_id: Mapped[str | None]


    user_id: Mapped[str | None]


    event_type: Mapped[str]


    entity: Mapped[str]


    entity_id: Mapped[str]


    timestamp: Mapped[datetime]