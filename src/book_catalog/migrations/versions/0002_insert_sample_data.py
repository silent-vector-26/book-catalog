"""Insert sample authors and books."""

from decimal import Decimal
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_sample_data"
down_revision: Union[str, None] = "0001_catalog"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

authors = sa.table(
    "authors",
    sa.column("id", sa.Integer),
    sa.column("name", sa.String),
    sa.column("country", sa.String),
)
books = sa.table(
    "books",
    sa.column("id", sa.Integer),
    sa.column("title", sa.String),
    sa.column("year", sa.Integer),
    sa.column("price", sa.Numeric(12, 2)),
    sa.column("author_id", sa.Integer),
)


def upgrade() -> None:
    op.bulk_insert(
        authors,
        [
            {"id": 1, "name": "J. R. R. Tolkien", "country": "United Kingdom"},
            {"id": 2, "name": "Ursula K. Le Guin", "country": "United States"},
            {"id": 3, "name": "George Orwell", "country": "United Kingdom"},
        ],
    )
    op.bulk_insert(
        books,
        [
            {
                "id": 1,
                "title": "The Hobbit",
                "year": 1937,
                "price": Decimal("12.99"),
                "author_id": 1,
            },
            {
                "id": 2,
                "title": "The Fellowship of the Ring",
                "year": 1954,
                "price": Decimal("14.99"),
                "author_id": 1,
            },
            {
                "id": 3,
                "title": "A Wizard of Earthsea",
                "year": 1968,
                "price": Decimal("10.99"),
                "author_id": 2,
            },
            {
                "id": 4,
                "title": "The Left Hand of Darkness",
                "year": 1969,
                "price": Decimal("11.50"),
                "author_id": 2,
            },
            {
                "id": 5,
                "title": "Nineteen Eighty-Four",
                "year": 1949,
                "price": Decimal("9.99"),
                "author_id": 3,
            },
        ],
    )
    op.execute(
        sa.text(
            "SELECT setval(pg_get_serial_sequence('authors', 'id'), "
            "(SELECT max(id) FROM authors))"
        )
    )
    op.execute(
        sa.text(
            "SELECT setval(pg_get_serial_sequence('books', 'id'), "
            "(SELECT max(id) FROM books))"
        )
    )


def downgrade() -> None:
    op.execute(books.delete().where(books.c.id.in_([1, 2, 3, 4, 5])))
    op.execute(authors.delete().where(authors.c.id.in_([1, 2, 3])))
