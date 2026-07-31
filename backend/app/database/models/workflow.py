from __future__ import annotations

from datetime import datetime, UTC

from sqlalchemy import JSON
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.database.base import Base


class Workflow(Base):

    __tablename__ = "workflows"


    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )


    goal: Mapped[str]

    description: Mapped[str | None] = mapped_column(nullable=True)

    assigned_agent: Mapped[str | None] = mapped_column(nullable=True)

    trigger_type: Mapped[str] = mapped_column(default="MANUAL")

    definition: Mapped[dict] = mapped_column(JSON, default=dict)


    status: Mapped[str] = mapped_column(
        default="CREATED",
    )


    created_by: Mapped[str]


    created_at: Mapped[datetime] = mapped_column(
        default=lambda:
            datetime.now(UTC),
    )


    completed_at: Mapped[
        datetime | None
    ] = mapped_column(
        nullable=True,
    )
