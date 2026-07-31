from __future__ import annotations

from datetime import datetime, UTC

from sqlalchemy import JSON
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.database.base import Base


class Action(Base):

    __tablename__ = "actions"


    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )


    name: Mapped[str]


    type: Mapped[str]


    permissions: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
    )
    status: Mapped[str] = mapped_column(default="ENABLED")
    usage: Mapped[int] = mapped_column(default=0)


    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC)
    )
