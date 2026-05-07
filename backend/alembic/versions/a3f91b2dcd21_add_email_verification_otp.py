"""Add email_verified + email_verification_tokens

Revision ID: a3f91b2dcd21
Revises: 9668ed2444f2
Create Date: 2026-05-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a3f91b2dcd21"
down_revision: Union[str, None] = "9668ed2444f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.text("1")),
    )
    op.create_table(
        "email_verification_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("otp_hash", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("failed_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
        sa.Column("last_sent_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_email_verification_tokens_email", "email_verification_tokens", ["email"], unique=False)
    op.create_index("ix_email_verification_tokens_user_id", "email_verification_tokens", ["user_id"], unique=False)
    op.create_index(op.f("ix_email_verification_tokens_id"), "email_verification_tokens", ["id"], unique=False)
    op.alter_column("users", "email_verified", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_email_verification_tokens_email", table_name="email_verification_tokens")
    op.drop_index("ix_email_verification_tokens_user_id", table_name="email_verification_tokens")
    op.drop_index(op.f("ix_email_verification_tokens_id"), table_name="email_verification_tokens")
    op.drop_table("email_verification_tokens")
    op.drop_column("users", "email_verified")
