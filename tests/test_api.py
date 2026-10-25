import asyncio

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient

from book_catalog.main import app


@pytest.fixture
async def client():
    await asyncio.to_thread(command.upgrade, Config("alembic.ini"), "head")
    async with app.router.lifespan_context(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as test_client:
            yield test_client


@pytest.mark.asyncio
async def test_book_and_author_crud_and_summary(client: AsyncClient):
    author_response = await client.post(
        "/api/authors",
        json={"name": "Test Author", "country": "Test Country"},
    )
    assert author_response.status_code == 201
    author = author_response.json()
    author_id = author["id"]
    book_id: int | None = None

    try:
        book_response = await client.post(
            "/api/books",
            json={
                "title": "Test Book",
                "year": 2020,
                "price": "12.99",
                "author_id": author_id,
            },
        )
        assert book_response.status_code == 201
        book = book_response.json()
        book_id = book["id"]
        assert (await client.get(f"/api/books/{book_id}")).json()["title"] == "Test Book"
        assert book_id in [
            item["id"] for item in (await client.get("/api/books")).json()
        ]
        assert (
            await client.get(f"/api/authors/{author_id}")
        ).json()["name"] == "Test Author"
        assert author_id in [
            item["id"] for item in (await client.get("/api/authors")).json()
        ]

        summary = await client.get("/api/books/summary")
        assert summary.status_code == 200
        assert {
            "id": book_id,
            "title": "Test Book",
            "author": "Test Author",
            "price": "12.99",
        } in summary.json()

        assert (await client.delete(f"/api/authors/{author_id}")).status_code == 409

        updated_book = await client.put(
            f"/api/books/{book_id}",
            json={
                "title": "Updated Book",
                "year": None,
                "price": "0.00",
                "author_id": author_id,
            },
        )
        assert updated_book.status_code == 200
        assert updated_book.json()["title"] == "Updated Book"

        assert (await client.delete(f"/api/books/{book_id}")).status_code == 204
        assert (await client.get(f"/api/books/{book_id}")).status_code == 404

        updated_author = await client.put(
            f"/api/authors/{author_id}",
            json={"name": "Updated Author", "country": None},
        )
        assert updated_author.status_code == 200
        assert updated_author.json()["name"] == "Updated Author"
    finally:
        if book_id is not None:
            await client.delete(f"/api/books/{book_id}")
        await client.delete(f"/api/authors/{author_id}")


@pytest.mark.asyncio
async def test_request_validation_and_missing_resources(client: AsyncClient):
    assert (await client.get("/")).status_code == 200
    assert (await client.get("/static/app.js")).status_code == 200

    invalid_author = await client.post("/api/authors", json={"name": "   "})
    assert invalid_author.status_code == 422

    invalid_book = await client.post(
        "/api/books",
        json={"title": "Bad Price", "price": "-1.00", "author_id": 1},
    )
    assert invalid_book.status_code == 422

    assert (await client.get("/api/books/2147483647")).status_code == 404
    assert (
        await client.put(
            "/api/authors/2147483647",
            json={"name": "Missing Author", "country": None},
        )
    ).status_code == 404
    assert (
        await client.put(
            "/api/authors/2147483647",
            json={"name": "Missing Author"},
        )
    ).status_code == 422


@pytest.mark.asyncio
async def test_sample_catalog_is_available(client: AsyncClient):
    authors = (await client.get("/api/authors")).json()
    books = (await client.get("/api/books")).json()
    assert {author["name"] for author in authors} >= {
        "J. R. R. Tolkien",
        "Ursula K. Le Guin",
        "George Orwell",
    }
    assert {book["title"] for book in books} >= {
        "The Hobbit",
        "The Fellowship of the Ring",
        "A Wizard of Earthsea",
        "The Left Hand of Darkness",
        "Nineteen Eighty-Four",
    }
