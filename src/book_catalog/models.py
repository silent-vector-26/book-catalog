from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
)

metadata = MetaData()

authors = Table(
    "authors",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False),
    Column("country", String, nullable=True),
    CheckConstraint("length(trim(name)) > 0", name="ck_authors_name_nonempty"),
)

books = Table(
    "books",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("title", String, nullable=False),
    Column("year", Integer, nullable=True),
    Column("price", Numeric(12, 2), nullable=False),
    Column(
        "author_id",
        ForeignKey("authors.id", ondelete="RESTRICT", name="books_author_id_fkey"),
        nullable=False,
    ),
    CheckConstraint("length(trim(title)) > 0", name="ck_books_title_nonempty"),
    CheckConstraint("year IS NULL OR year > 0", name="ck_books_year_positive"),
    CheckConstraint("price >= 0", name="ck_books_price_nonnegative"),
)
