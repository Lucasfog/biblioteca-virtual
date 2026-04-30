from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "authors",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("name", name="uq_authors_name"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    op.create_table(
        "books",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("isbn", sa.String(length=32), nullable=False),
        sa.Column("total_copies", sa.Integer(), nullable=False),
        sa.Column("available_copies", sa.Integer(), nullable=False),
        sa.Column(
            "author_id",
            sa.UUID(),
            sa.ForeignKey("authors.id"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("total_copies >= 0", name="ck_books_total_nonnegative"),
        sa.CheckConstraint(
            "available_copies >= 0", name="ck_books_available_nonnegative"
        ),
        sa.CheckConstraint(
            "available_copies <= total_copies", name="ck_books_available_le_total"
        ),
        sa.UniqueConstraint("isbn", name="uq_books_isbn"),
    )

    loan_status = postgresql.ENUM("ACTIVE", "RETURNED", name="loanstatus")
    loan_status.create(op.get_bind(), checkfirst=True)
    loan_status_no_create = postgresql.ENUM(
        "ACTIVE", "RETURNED", name="loanstatus", create_type=False
    )

    op.create_table(
        "loans",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("book_id", sa.UUID(), sa.ForeignKey("books.id"), nullable=False),
        sa.Column("status", loan_status_no_create, nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("returned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "fine_cents",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_authors_name", "authors", ["name"], unique=True)
    op.create_index("ix_books_isbn", "books", ["isbn"], unique=True)
    op.create_index("ix_books_author_id", "books", ["author_id"])
    op.create_index("ix_loans_user_id", "loans", ["user_id"])
    op.create_index("ix_loans_book_id", "loans", ["book_id"])
    op.create_index("ix_loans_status", "loans", ["status"])


def downgrade() -> None:
    op.drop_index("ix_loans_status", table_name="loans")
    op.drop_index("ix_loans_book_id", table_name="loans")
    op.drop_index("ix_loans_user_id", table_name="loans")
    op.drop_table("loans")

    op.drop_index("ix_books_author_id", table_name="books")
    op.drop_index("ix_books_isbn", table_name="books")
    op.drop_table("books")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    op.drop_index("ix_authors_name", table_name="authors")
    op.drop_table("authors")

    loan_status = postgresql.ENUM("ACTIVE", "RETURNED", name="loanstatus")
    loan_status.drop(op.get_bind(), checkfirst=True)
