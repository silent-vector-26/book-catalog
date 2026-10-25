# Book Catalog

A simple full-stack Book Catalog application for exploring modern Python web development.

This project is a small research and learning environment for evaluating Python, asynchronous programming, REST APIs, PostgreSQL access, validation, testing, and common application patterns.

## Goals

The application demonstrates:

- REST API development
- Asynchronous database access
- CRUD operations
- SQL queries and projections
- Data validation and typed models
- PostgreSQL integration
- Simple web frontend
- Automated testing
- Dependency and environment management

## Tech Stack

- Python
- FastAPI
- Pydantic
- SQLAlchemy Core
- asyncpg
- PostgreSQL
- Jinja2
- pytest
- uv
- Docker / Docker Compose

## Domain

The application manages authors and books.

### Author

- `id`
- `name`
- `country`

### Book

- `id`
- `title`
- `year`
- `price`
- `author_id`

An author can have multiple books.

## API

The application provides CRUD operations for books and authors, plus a joined
book-summary projection:

```text
GET    /api/books
GET    /api/books/{id}
POST   /api/books
PUT    /api/books/{id}
DELETE /api/books/{id}
GET    /api/books/summary

GET    /api/authors
GET    /api/authors/{id}
POST   /api/authors
PUT    /api/authors/{id}
DELETE /api/authors/{id}
```

`PUT` replaces the complete editable representation. Lists are ordered by ID
and are not paginated. Invalid data receives FastAPI's standard `422` response;
deleting an author who still has books returns `409 Conflict`.

## Local development

Prerequisites: Python 3.12 or newer, `uv`, and Docker Compose.

```powershell
Copy-Item .env.example .env
docker compose up -d
uv sync --extra dev
uv run alembic upgrade head
uv run uvicorn book_catalog.main:app --reload --app-dir src
```

Alembic creates the database schema and inserts the sample authors and books.
The application does not change the schema on startup. After changing the
schema, generate a migration with `uv run alembic revision --autogenerate -m
"describe change"`, review the generated file, and apply it with
`uv run alembic upgrade head`. Roll back one migration with
`uv run alembic downgrade -1`. API documentation is available at
`http://127.0.0.1:8000/docs`.

If upgrading a local database created by the earlier `create_all` startup
behavior, preserve its existing schema and mark it as the initial revision
before applying the sample-data migration:

```powershell
uv run alembic stamp 0001_catalog
uv run alembic upgrade head
```

Run the API and frontend tests with:

```powershell
uv run pytest
```
