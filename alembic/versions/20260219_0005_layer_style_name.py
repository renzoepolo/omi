"""add style_name to layers

Revision ID: 20260219_0005
Revises: 20260219_0004
Create Date: 2026-02-19 00:00:01.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260219_0005"
down_revision: Union[str, None] = "20260219_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("layers", sa.Column("style_name", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("layers", "style_name")
