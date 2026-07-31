from __future__ import annotations

from datetime import datetime, UTC

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.database.base import Base


class Agent(Base):

    __tablename__ = "agents"


    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )


    name: Mapped[str] = mapped_column(
        unique=True,
        nullable=False,
    )


    status: Mapped[str] = mapped_column(
        default="CREATED",
    )


    health: Mapped[str] = mapped_column(
        default="UNKNOWN",
    )


    configuration: Mapped[str] = mapped_column(
        default="{}",
    )


    created_at: Mapped[datetime] = mapped_column(
        default=lambda:
            datetime.now(UTC),
    )