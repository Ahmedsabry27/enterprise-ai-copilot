"""add workflow definition
Revision ID: c6e8f0a2b4d6
Revises: b4d6e8f0a2c4
"""
from alembic import op
import sqlalchemy as sa
revision="c6e8f0a2b4d6"
down_revision="b4d6e8f0a2c4"
branch_labels=None
depends_on=None
def upgrade(): op.add_column("workflows",sa.Column("definition",sa.JSON(),nullable=False,server_default="{}"));op.alter_column("workflows","definition",server_default=None)
def downgrade(): op.drop_column("workflows","definition")
