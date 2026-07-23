"""add user_id to conversations

Revision ID: 0e0b5d2ac24a
Revises: fd8b5f55d5e1
Create Date: 2026-07-23 12:38:36.006076

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0e0b5d2ac24a"
down_revision: Union[str, Sequence[str], None] = "fd8b5f55d5e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "conversations",
        sa.Column(
            "user_id",
            sa.String(length=255),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_conversations_user_id",
        "conversations",
        ["user_id"],
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        "ix_conversations_user_id",
        table_name="conversations",
    )

    op.drop_column(
        "conversations",
        "user_id",
    )