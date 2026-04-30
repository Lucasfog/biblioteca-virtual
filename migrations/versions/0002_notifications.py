"""Add notification tracking table.

Revision ID: 0002_notifications
Revises: 0001_initial
Create Date: 2026-04-29 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_notifications"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "loan_notifications",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column("loan_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "type",
            sa.String(length=50),
            nullable=False,
            comment="due_soon | overdue",
        ),
        sa.Column(
            "channel",
            sa.String(length=50),
            nullable=False,
            comment="email | webhook",
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="pending",
            comment="pending | sent | failed",
        ),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["loan_id"], ["loans.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )

    op.create_index(
        "ix_loan_notifications_loan_id",
        "loan_notifications",
        ["loan_id"],
    )
    op.create_index(
        "ix_loan_notifications_user_id",
        "loan_notifications",
        ["user_id"],
    )
    op.create_index(
        "ix_loan_notifications_status",
        "loan_notifications",
        ["status"],
    )
    op.create_index(
        "ix_loan_notifications_created_at",
        "loan_notifications",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_loan_notifications_created_at", table_name="loan_notifications")
    op.drop_index("ix_loan_notifications_status", table_name="loan_notifications")
    op.drop_index("ix_loan_notifications_user_id", table_name="loan_notifications")
    op.drop_index("ix_loan_notifications_loan_id", table_name="loan_notifications")
    op.drop_table("loan_notifications")
