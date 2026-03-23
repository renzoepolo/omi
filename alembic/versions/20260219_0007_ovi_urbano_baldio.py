"""add ovi urbano baldio table

Revision ID: 20260219_0007
Revises: 20260219_0006
Create Date: 2026-02-19 00:00:03.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260219_0007"
down_revision: Union[str, None] = "20260219_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "observation_ovi_urbano_baldio",
        sa.Column("observation_id", sa.Uuid(), nullable=False),
        sa.Column("tipo_inmueble", sa.Integer(), nullable=False),
        sa.Column("origen_valor", sa.Integer(), nullable=False),
        sa.Column("superficie", sa.Integer(), nullable=False),
        sa.Column("uni_sup", sa.Integer(), nullable=False),
        sa.Column("moneda", sa.Integer(), nullable=False),
        sa.Column("valor_total", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("nomenclatura", sa.String(length=255), nullable=False),
        sa.Column("afectacion", sa.Integer(), nullable=False),
        sa.Column("frente", sa.Integer(), nullable=False),
        sa.Column("forma", sa.Integer(), nullable=False),
        sa.Column("ubic_cuadra", sa.Integer(), nullable=False),
        sa.Column("tipo_barrio", sa.Integer(), nullable=False),
        sa.Column("sit_juridica", sa.Integer(), nullable=False),
        sa.Column("fecha_valor", sa.Date(), nullable=False),
        sa.Column("procedencia", sa.Integer(), nullable=False),
        sa.Column("telefono", sa.String(length=255), nullable=True),
        sa.Column("foto_fachada", sa.String(length=1024), nullable=True),
        sa.Column("foto_cartel", sa.String(length=1024), nullable=True),
        sa.Column("link", sa.String(length=1024), nullable=True),
        sa.ForeignKeyConstraint(["observation_id"], ["observations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("observation_id"),
    )


def downgrade() -> None:
    op.drop_table("observation_ovi_urbano_baldio")
