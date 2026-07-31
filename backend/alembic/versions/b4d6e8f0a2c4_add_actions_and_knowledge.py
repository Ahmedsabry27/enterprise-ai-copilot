"""add action status and knowledge sources
Revision ID: b4d6e8f0a2c4
Revises: a2c5e7d9f1b3
"""
from alembic import op
import sqlalchemy as sa
revision="b4d6e8f0a2c4"
down_revision="a2c5e7d9f1b3"
branch_labels=None
depends_on=None
def upgrade():
    op.add_column("actions", sa.Column("status", sa.String(), nullable=False, server_default="ENABLED"))
    op.add_column("actions", sa.Column("usage", sa.Integer(), nullable=False, server_default="0"))
    op.alter_column("actions", "status", server_default=None); op.alter_column("actions", "usage", server_default=None)
    op.create_table("knowledge_sources",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("name",sa.String(),nullable=False),sa.Column("source_type",sa.String(),nullable=False),sa.Column("location",sa.String(),nullable=True),sa.Column("created_at",sa.DateTime(),nullable=False))
def downgrade():
    op.drop_table("knowledge_sources");op.drop_column("actions","usage");op.drop_column("actions","status")
