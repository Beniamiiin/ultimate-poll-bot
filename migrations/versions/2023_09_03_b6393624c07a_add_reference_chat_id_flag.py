"""add reference chat_id flag

Revision ID: b6393624c07a
Revises: 0abcfa34e032
Create Date: 2023-09-03 11:53:45.469244

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b6393624c07a'
down_revision = '0abcfa34e032'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("reference", sa.Column("chat_id", sa.BigInteger(), nullable=True))


def downgrade():
    op.drop_column("reference", "chat_id")
