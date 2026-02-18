"""OVI phase 2 detail tables

Revision ID: 20260218_0003
Revises: 20260218_0002
Create Date: 2026-02-18 00:00:01.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260218_0003"
down_revision: Union[str, None] = "20260218_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "observation_location",
        sa.Column("observation_id", sa.Uuid(), nullable=False),
        sa.Column("padron", sa.String(length=255), nullable=True),
        sa.Column("neighborhood_type_code", sa.String(length=64), nullable=True),
        sa.Column("shape_type_code", sa.String(length=64), nullable=True),
        sa.Column("block_position_code", sa.String(length=64), nullable=True),
        sa.Column("legal_status_id", sa.Integer(), nullable=True),
        sa.Column("affectation_code", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(["legal_status_id"], ["catalog_legal_status.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["observation_id"], ["observations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("observation_id"),
    )
    op.create_index("ix_observation_location_padron", "observation_location", ["padron"], unique=False)

    op.create_table(
        "observation_building",
        sa.Column("observation_id", sa.Uuid(), nullable=False),
        sa.Column("built_surface_total", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("warehouse_surface", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("front_meters", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("conservation_state_id", sa.Integer(), nullable=True),
        sa.Column("destination_id", sa.Integer(), nullable=True),
        sa.Column("construction_category_code", sa.String(length=64), nullable=True),
        sa.Column("bedrooms_count", sa.Integer(), nullable=True),
        sa.Column("bathrooms_count", sa.Integer(), nullable=True),
        sa.Column("garage_count", sa.Integer(), nullable=True),
        sa.Column("floors_count", sa.Integer(), nullable=True),
        sa.Column("has_pool", sa.Boolean(), nullable=True),
        sa.Column("antiquity_year", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["conservation_state_id"], ["catalog_conservation_state.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["destination_id"], ["catalog_destination.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["observation_id"], ["observations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("observation_id"),
    )

    op.create_table(
        "observation_rural",
        sa.Column("observation_id", sa.Uuid(), nullable=False),
        sa.Column("main_use_code", sa.String(length=64), nullable=True),
        sa.Column("sugarcane_surface", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("citrus_surface", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("grains_surface", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("forest_surface", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("other_crops_surface", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("has_irrigation", sa.Boolean(), nullable=True),
        sa.Column("irrigation_type_code", sa.String(length=64), nullable=True),
        sa.Column("irrigated_surface", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("irrigation_concession_type_code", sa.String(length=64), nullable=True),
        sa.Column("has_extraordinary_improvements", sa.Boolean(), nullable=True),
        sa.Column("has_rural_improvements", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["observation_id"], ["observations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("observation_id"),
    )


def downgrade() -> None:
    op.drop_table("observation_rural")
    op.drop_table("observation_building")
    op.drop_index("ix_observation_location_padron", table_name="observation_location")
    op.drop_table("observation_location")
