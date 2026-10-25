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

The application will provide standard CRUD operations such as:

```text
GET    /api/books
GET    /api/books/{id}
POST   /api/books
PUT    /api/books/{id}
DELETE /api/books/{id}

GET    /api/authors
POST   /api/authors
