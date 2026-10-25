from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncConnection

from book_catalog.database import engine, get_connection
from book_catalog.repositories import (
    create_author,
    create_book,
    delete_author,
    delete_book,
    get_author,
    get_book,
    list_authors,
    list_book_summaries,
    list_books,
    update_author,
    update_book,
)
from book_catalog.schemas import (
    AuthorCreate,
    AuthorResponse,
    AuthorUpdate,
    BookCreate,
    BookResponse,
    BookSummary,
    BookUpdate,
)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await engine.dispose()


app = FastAPI(title="Book Catalog", lifespan=lifespan)
app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent / "static"),
    name="static",
)
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )


@app.get("/api/books", response_model=list[BookResponse])
async def books_list(connection: AsyncConnection = Depends(get_connection)):
    return await list_books(connection)


@app.get("/api/books/summary", response_model=list[BookSummary])
async def books_summary(connection: AsyncConnection = Depends(get_connection)):
    return await list_book_summaries(connection)


@app.get("/api/books/{book_id}", response_model=BookResponse)
async def book_get(book_id: int, connection: AsyncConnection = Depends(get_connection)):
    book = await get_book(connection, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@app.post("/api/books", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def book_create(
    payload: BookCreate, connection: AsyncConnection = Depends(get_connection)
):
    book = await create_book(connection, payload)
    if book is None:
        raise HTTPException(status_code=404, detail="Author not found")
    return book


@app.put("/api/books/{book_id}", response_model=BookResponse)
async def book_update(
    book_id: int,
    payload: BookUpdate,
    connection: AsyncConnection = Depends(get_connection),
):
    book = await update_book(connection, book_id, payload)
    if book is None:
        if await get_book(connection, book_id) is None:
            raise HTTPException(status_code=404, detail="Book not found")
        raise HTTPException(status_code=404, detail="Author not found")
    return book


@app.delete("/api/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def book_delete(book_id: int, connection: AsyncConnection = Depends(get_connection)):
    if not await delete_book(connection, book_id):
        raise HTTPException(status_code=404, detail="Book not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/api/authors", response_model=list[AuthorResponse])
async def authors_list(connection: AsyncConnection = Depends(get_connection)):
    return await list_authors(connection)


@app.get("/api/authors/{author_id}", response_model=AuthorResponse)
async def author_get(
    author_id: int, connection: AsyncConnection = Depends(get_connection)
):
    author = await get_author(connection, author_id)
    if author is None:
        raise HTTPException(status_code=404, detail="Author not found")
    return author


@app.post(
    "/api/authors", response_model=AuthorResponse, status_code=status.HTTP_201_CREATED
)
async def author_create(
    payload: AuthorCreate, connection: AsyncConnection = Depends(get_connection)
):
    return await create_author(connection, payload)


@app.put("/api/authors/{author_id}", response_model=AuthorResponse)
async def author_update(
    author_id: int,
    payload: AuthorUpdate,
    connection: AsyncConnection = Depends(get_connection),
):
    author = await update_author(connection, author_id, payload)
    if author is None:
        raise HTTPException(status_code=404, detail="Author not found")
    return author


@app.delete("/api/authors/{author_id}", status_code=status.HTTP_204_NO_CONTENT)
async def author_delete(
    author_id: int, connection: AsyncConnection = Depends(get_connection)
):
    result = await delete_author(connection, author_id)
    if result == "missing":
        raise HTTPException(status_code=404, detail="Author not found")
    if result == "conflict":
        raise HTTPException(
            status_code=409, detail="Cannot delete an author with associated books"
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
