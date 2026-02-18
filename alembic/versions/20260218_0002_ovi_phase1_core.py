"""OVI phase 1 core schema

Revision ID: 20260218_0002
Revises: 20261018_0001
Create Date: 2026-02-18 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260218_0002"
down_revision: Union[str, None] = "20261018_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


observation_status = sa.Enum(
    "cargado",
    "posicionado",
    "revision",
    "completado",
    "outlier",
    "eliminado",
    name="observation_status",
    native_enum=False,
)


def upgrade() -> None:
    observation_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "catalog_property_type",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1024), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "catalog_currency",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=16), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1024), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "catalog_value_origin",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1024), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "catalog_legal_status",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1024), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "catalog_destination",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1024), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "catalog_conservation_state",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1024), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "observations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("external_uuid", sa.Uuid(), nullable=True),
        sa.Column("legacy_fid", sa.Integer(), nullable=True),
        sa.Column("property_type_id", sa.Integer(), nullable=False),
        sa.Column("value_origin_id", sa.Integer(), nullable=True),
        sa.Column("currency_id", sa.Integer(), nullable=True),
        sa.Column("market_value_total", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("unit_land_value", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("valuation_date", sa.Date(), nullable=True),
        sa.Column("surface_total", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("surface_unit", sa.String(length=16), nullable=False, server_default="m2"),
        sa.Column("status", observation_status, nullable=False, server_default="cargado"),
        sa.Column("is_outlier", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("extras", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["currency_id"], ["catalog_currency.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["property_type_id"], ["catalog_property_type.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["value_origin_id"], ["catalog_value_origin.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "external_uuid", name="uq_observations_project_external_uuid"),
    )
    op.create_index("ix_observations_project_id", "observations", ["project_id"], unique=False)
    op.create_index("ix_observations_status", "observations", ["status"], unique=False)
    op.create_index("ix_observations_deleted_at", "observations", ["deleted_at"], unique=False)
    op.create_index("ix_observations_project_status", "observations", ["project_id", "status"], unique=False)

    op.create_table(
        "observation_status_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("observation_id", sa.Uuid(), nullable=False),
        sa.Column("from_status", observation_status, nullable=True),
        sa.Column("to_status", observation_status, nullable=False),
        sa.Column("changed_by", sa.Integer(), nullable=True),
        sa.Column("reason", sa.String(length=1024), nullable=True),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["observation_id"], ["observations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_observation_status_history_observation_id",
        "observation_status_history",
        ["observation_id"],
        unique=False,
    )

    op.bulk_insert(
        sa.table(
            "catalog_property_type",
            sa.column("code", sa.String),
            sa.column("label", sa.String),
            sa.column("description", sa.String),
            sa.column("is_active", sa.Boolean),
            sa.column("sort_order", sa.Integer),
        ),
        [
            {"code": "urbano_baldio", "label": "Urbano Baldio", "description": None, "is_active": True, "sort_order": 1},
            {
                "code": "urbano_edificado",
                "label": "Urbano Edificado",
                "description": "Incluye PH en migracion legacy",
                "is_active": True,
                "sort_order": 2,
            },
            {"code": "rural", "label": "Rural", "description": None, "is_active": True, "sort_order": 3},
        ],
    )
    op.bulk_insert(
        sa.table(
            "catalog_currency",
            sa.column("code", sa.String),
            sa.column("label", sa.String),
            sa.column("description", sa.String),
            sa.column("is_active", sa.Boolean),
            sa.column("sort_order", sa.Integer),
        ),
        [
            {"code": "ARS", "label": "Pesos", "description": "Peso argentino", "is_active": True, "sort_order": 1},
            {"code": "USD", "label": "Dolares", "description": "Dolar estadounidense", "is_active": True, "sort_order": 2},
        ],
    )
    op.bulk_insert(
        sa.table(
            "catalog_value_origin",
            sa.column("code", sa.String),
            sa.column("label", sa.String),
            sa.column("description", sa.String),
            sa.column("is_active", sa.Boolean),
            sa.column("sort_order", sa.Integer),
        ),
        [
            {"code": "oferta", "label": "Oferta", "description": None, "is_active": True, "sort_order": 1},
            {"code": "venta", "label": "Venta", "description": None, "is_active": True, "sort_order": 2},
            {"code": "escrituracion", "label": "Escrituracion", "description": None, "is_active": True, "sort_order": 3},
            {"code": "tasacion", "label": "Tasacion", "description": None, "is_active": True, "sort_order": 4},
            {
                "code": "valor_referencia",
                "label": "Valor de Referencia",
                "description": None,
                "is_active": True,
                "sort_order": 5,
            },
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_observation_status_history_observation_id", table_name="observation_status_history")
    op.drop_table("observation_status_history")

    op.drop_index("ix_observations_project_status", table_name="observations")
    op.drop_index("ix_observations_deleted_at", table_name="observations")
    op.drop_index("ix_observations_status", table_name="observations")
    op.drop_index("ix_observations_project_id", table_name="observations")
    op.drop_table("observations")

    op.drop_table("catalog_conservation_state")
    op.drop_table("catalog_destination")
    op.drop_table("catalog_legal_status")
    op.drop_table("catalog_value_origin")
    op.drop_table("catalog_currency")
    op.drop_table("catalog_property_type")

    observation_status.drop(op.get_bind(), checkfirst=True)
