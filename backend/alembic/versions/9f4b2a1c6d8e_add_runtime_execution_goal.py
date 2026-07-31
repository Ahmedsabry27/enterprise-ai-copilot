"""add runtime execution goal

Revision ID: 9f4b2a1c6d8e
Revises: 8c3d1f0b2a6e
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9f4b2a1c6d8e"
down_revision: Union[str, Sequence[str], None] = "8c3d1f0b2a6e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("runtime_executions", sa.Column("goal", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("runtime_executions", "goal")
