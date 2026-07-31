"""add workflow management fields

Revision ID: a2c5e7d9f1b3
Revises: 9f4b2a1c6d8e
"""

from alembic import op
import sqlalchemy as sa

revision = "a2c5e7d9f1b3"
down_revision = "9f4b2a1c6d8e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("workflows", sa.Column("description", sa.String(), nullable=True))
    op.add_column("workflows", sa.Column("assigned_agent", sa.String(), nullable=True))
    op.add_column("workflows", sa.Column("trigger_type", sa.String(), nullable=False, server_default="MANUAL"))
    op.alter_column("workflows", "trigger_type", server_default=None)


def downgrade() -> None:
    op.drop_column("workflows", "trigger_type")
    op.drop_column("workflows", "assigned_agent")
    op.drop_column("workflows", "description")
