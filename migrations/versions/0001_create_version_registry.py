"""create immutable version registry tables

Revision ID: 0001
Revises:
Create Date: 2026-11-23

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "verifier_versions",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", _TS, server_default=sa.func.now(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "task_versions",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", _TS, server_default=sa.func.now(), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("verifier_version_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["verifier_version_id"], ["verifier_versions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "agent_versions",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", _TS, server_default=sa.func.now(), nullable=False),
        sa.Column("adapter_name", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "environment_versions",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", _TS, server_default=sa.func.now(), nullable=False),
        sa.Column("image_digest", sa.String(length=255), nullable=False),
        sa.Column("platform", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "runtime_profile_revisions",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", _TS, server_default=sa.func.now(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("isolation_class", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("runtime_profile_revisions")
    op.drop_table("environment_versions")
    op.drop_table("agent_versions")
    op.drop_table("task_versions")
    op.drop_table("verifier_versions")
