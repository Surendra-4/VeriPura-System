"""Add auth fields to users

Revision ID: 20260216_0002
Revises: 20260215_0001
Create Date: 2026-02-16 00:00:00

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260216_0002"
down_revision: Union[str, None] = "20260215_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


user_role_enum = sa.Enum(
    "ADMIN",
    "IMPORTER",
    "EXPORTER",
    "LAB",
    name="user_role_enum",
    native_enum=False,
)


def upgrade() -> None:
    op.add_column("users", sa.Column("hashed_password", sa.String(length=255), nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "role",
            user_role_enum,
            nullable=False,
            server_default="IMPORTER",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "auth_provider",
            sa.String(length=32),
            nullable=False,
            server_default="local",
        ),
    )
    op.add_column("users", sa.Column("google_sub", sa.String(length=255), nullable=True))

    op.create_unique_constraint("uq_users_google_sub", "users", ["google_sub"])
    op.create_check_constraint(
        "ck_users_auth_provider",
        "users",
        "auth_provider IN ('local', 'google')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_users_auth_provider", "users", type_="check")
    op.drop_constraint("uq_users_google_sub", "users", type_="unique")

    op.drop_column("users", "google_sub")
    op.drop_column("users", "auth_provider")
    op.drop_column("users", "is_active")
    op.drop_column("users", "role")
    op.drop_column("users", "hashed_password")
