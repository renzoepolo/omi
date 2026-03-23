"""admin backend entities

Revision ID: 20260219_0004
Revises: 20260218_0003
Create Date: 2026-02-19 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260219_0004"
down_revision: Union[str, None] = "20260218_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


layer_type = sa.Enum("WMS", "WFS", name="layer_type", native_enum=False)


def upgrade() -> None:
    op.add_column("projects", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("projects", sa.Column("default_center_lng", sa.Float(), nullable=True))
    op.add_column("projects", sa.Column("default_center_lat", sa.Float(), nullable=True))
    op.add_column("projects", sa.Column("default_zoom", sa.Integer(), nullable=False, server_default="13"))

    layer_type.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "layers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("geoserver_workspace", sa.String(length=255), nullable=False),
        sa.Column("geoserver_layer_name", sa.String(length=255), nullable=False),
        sa.Column("type", layer_type, nullable=False),
        sa.Column("default_visible", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("z_index", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "project_layers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("layer_id", sa.Integer(), nullable=False),
        sa.Column("visible_override", sa.Boolean(), nullable=True),
        sa.Column("z_index_override", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["layer_id"], ["layers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "layer_id", name="uq_project_layer"),
    )

    op.create_table(
        "form_field_definitions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("field_key", sa.String(length=128), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("field_type", sa.String(length=64), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("config", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "admin_audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("target_type", sa.String(length=128), nullable=False),
        sa.Column("target_id", sa.String(length=128), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.alter_column("projects", "default_zoom", server_default=None)


def downgrade() -> None:
    op.drop_table("admin_audit_logs")
    op.drop_table("form_field_definitions")
    op.drop_table("project_layers")
    op.drop_table("layers")
    layer_type.drop(op.get_bind(), checkfirst=True)

    op.drop_column("projects", "default_zoom")
    op.drop_column("projects", "default_center_lat")
    op.drop_column("projects", "default_center_lng")
    op.drop_column("projects", "description")
