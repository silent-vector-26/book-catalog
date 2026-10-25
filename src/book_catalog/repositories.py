from typing import Any

from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncConnection

from book_catalog.models import authors, books
from book_catalog.schemas import AuthorCreate, AuthorUpdate, BookCreate, BookUpdate


async def list_authors(connection: AsyncConnection) -> list[dict[str, Any]]:
    result = await connection.execute(select(authors).order_by(authors.c.id))
    return [dict(row) for row in result.mappings()]


async def get_author(connection: AsyncConnection, author_id: int) -> dict[str, Any] | None:
    result = await connection.execute(select(authors).where(authors.c.id == author_id))
    row = result.mappings().first()
    return dict(row) if row else None


async def create_author(connection: AsyncConnection, author: AuthorCreate) -> dict[str, Any]:
    result = await connection.execute(
        insert(authors).values(**author.model_dump()).returning(authors)
    )
    return dict(result.mappings().one())


async def update_author(
    connection: AsyncConnection, author_id: int, author: AuthorUpdate
) -> dict[str, Any] | None:
    result = await connection.execute(
        update(authors)
        .where(authors.c.id == author_id)
        .values(**author.model_dump())
        .returning(authors)
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def delete_author(connection: AsyncConnection, author_id: int) -> str:
    existing = await connection.execute(
        select(authors.c.id)
        .where(authors.c.id == author_id)
        .with_for_update()
    )
    if existing.first() is None:
        return "missing"

    has_books = await connection.execute(
        select(books.c.id).where(books.c.author_id == author_id).limit(1)
    )
    if has_books.first() is not None:
        return "conflict"

    await connection.execute(delete(authors).where(authors.c.id == author_id))
    return "deleted"


async def list_books(connection: AsyncConnection) -> list[dict[str, Any]]:
    result = await connection.execute(select(books).order_by(books.c.id))
    return [dict(row) for row in result.mappings()]


async def get_book(connection: AsyncConnection, book_id: int) -> dict[str, Any] | None:
    result = await connection.execute(select(books).where(books.c.id == book_id))
    row = result.mappings().first()
    return dict(row) if row else None


async def list_book_summaries(connection: AsyncConnection) -> list[dict[str, Any]]:
    statement = (
        select(
            books.c.id,
            books.c.title,
            authors.c.name.label("author"),
            books.c.price,
        )
        .join(authors, books.c.author_id == authors.c.id)
        .order_by(books.c.id)
    )
    result = await connection.execute(statement)
    return [dict(row) for row in result.mappings()]


async def _author_exists(connection: AsyncConnection, author_id: int) -> bool:
    result = await connection.execute(select(authors.c.id).where(authors.c.id == author_id))
    return result.first() is not None


async def create_book(connection: AsyncConnection, book: BookCreate) -> dict[str, Any] | None:
    if not await _author_exists(connection, book.author_id):
        return None
    result = await connection.execute(
        insert(books).values(**book.model_dump()).returning(books)
    )
    return dict(result.mappings().one())


async def update_book(
    connection: AsyncConnection, book_id: int, book: BookUpdate
) -> dict[str, Any] | None:
    if not await _author_exists(connection, book.author_id):
        return None
    result = await connection.execute(
        update(books)
        .where(books.c.id == book_id)
        .values(**book.model_dump())
        .returning(books)
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def delete_book(connection: AsyncConnection, book_id: int) -> bool:
    result = await connection.execute(delete(books).where(books.c.id == book_id))
    return result.rowcount > 0
