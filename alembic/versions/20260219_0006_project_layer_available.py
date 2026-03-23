"""add available_override to project_layers

Revision ID: 20260219_0006
Revises: 20260219_0005
Create Date: 2026-02-19 00:00:02.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260219_0006"
down_revision: Union[str, None] = "20260219_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("project_layers", sa.Column("available_override", sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column("project_layers", "available_override")
