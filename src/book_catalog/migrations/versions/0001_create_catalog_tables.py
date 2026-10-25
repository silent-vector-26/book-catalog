"""Create authors and books tables."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_catalog"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "authors",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("country", sa.String(), nullable=True),
        sa.CheckConstraint(
            "length(trim(name)) > 0", name="ck_authors_name_nonempty"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "books",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "length(trim(title)) > 0", name="ck_books_title_nonempty"
        ),
        sa.CheckConstraint(
            "year IS NULL OR year > 0", name="ck_books_year_positive"
        ),
        sa.CheckConstraint("price >= 0", name="ck_books_price_nonnegative"),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["authors.id"],
            name="books_author_id_fkey",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("books")
    op.drop_table("authors")
