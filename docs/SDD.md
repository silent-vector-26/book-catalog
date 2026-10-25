# Software Design Document
## Book Catalog

**Version:** 0.2
**Status:** Draft
**Related:** [SRS](../.docs/SRS.md) · [README](../README.md)

---

## 1. Changes

### 1.1 Document history

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-10-25 | Initial implementation: FastAPI + SQLAlchemy Core + asyncpg, CRUD, summary projection, Jinja2 frontend. |
| 0.2 | 2026-10-25 | Alembic migrations with sample data; schema no longer created at startup. |

### 1.2 Changes relative to the SRS

| # | Area | SRS | Design / implementation | Reason |
|---|---|---|---|---|
| 1 | `PUT` semantics | Unspecified | Full replacement; all editable fields required (`year` and `country` must be sent, may be `null`) | Agreed clarification |
| 2 | Delete author with books | "Shall handle" | `409 Conflict`; books never deleted automatically; FK is `ON DELETE RESTRICT` | Agreed clarification |
| 3 | Validation | Generic | Non-blank `name`/`title`; `price >= 0`, max 12 digits, 2 decimals; `year > 0` or `null` | Agreed clarification |
| 4 | Invalid requests | `400` or `422` | `422` only (FastAPI default) | Agreed clarification |
| 5 | Lists | Unspecified | JSON arrays ordered by `id`, no pagination | Agreed clarification |
| 6 | Price in JSON | Number (`12.99`) | Decimal string (`"12.99"`) | Avoid floating-point rounding; SRS examples updated |
| 7 | Schema management | Not specified | Alembic migrations (`0001_catalog`, `0002_sample_data`); no `create_all` at startup | New requirement DB-006 |
| 8 | Sample data | Not specified | 3 authors, 5 books seeded by migration `0002` | Demo usability |
| 9 | Project layout | Packages `models/`, `repositories/`, `api/` | Single modules: `models.py`, `repositories.py`, `api.py`, `schemas.py` | NFR-001 simplicity; SRS section 12 updated |
| 10 | Missing author on book create/update | Unspecified | `404 Author not found` | Consistent "referenced resource missing" rule |
| 11 | `DATABASE_URL` | Example only | Must use the `postgresql+asyncpg://` scheme | Required by async SQLAlchemy |
| 12 | Frontend | Jinja2 + JavaScript | One Jinja2 page (`index.html`) with a vanilla JS client calling the REST API | NFR-001 simplicity |

### 1.3 Known gaps against the SRS

| Requirement | Status |
|---|---|
| TEST-001 Unit tests | Not yet implemented; tests are API/integration only |
| DB-005 Transaction demo | Each request runs in one transaction, but no test demonstrates rollback |
| Error handling (section 9) | No custom `500` handler; unexpected errors use framework defaults |
| Test isolation | Tests run against the dev database (`DATABASE_URL`) and clean up their own rows |

---

## 2. Architecture

### 2.1 Component view

```mermaid
flowchart TB
    Browser["Web Browser"]

    subgraph App["book_catalog (FastAPI process)"]
        Static["static/app.js + styles.css"]
        Template["templates/index.html"]
        Api["api.py<br/>Routes + HTTP errors"]
        Schemas["schemas.py<br/>Pydantic models"]
        Repo["repositories.py<br/>SQLAlchemy Core queries"]
        Models["models.py<br/>Table definitions"]
        Db["database.py<br/>Async engine + connection dependency"]
        Config["config.py<br/>Settings (.env)"]
    end

    Alembic["Alembic<br/>migrations/"]
    PG[("PostgreSQL 17<br/>Docker Compose")]

    Browser -->|"GET /"| Template
    Browser -->|"GET /static/*"| Static
    Browser -->|"fetch /api/*"| Api
    Api --> Schemas
    Api --> Repo
    Repo --> Models
    Repo --> Db
    Db --> Config
    Db -->|"asyncpg"| PG
    Alembic --> Models
    Alembic --> Config
    Alembic -->|"DDL + seed"| PG
```

### 2.2 Module responsibilities

| Module | Responsibility |
|---|---|
| `main.py` | Exposes `app` for uvicorn |
| `api.py` | Routes, status codes, mapping repository results to HTTP errors, static files and template |
| `schemas.py` | Request/response/projection Pydantic models (public contract) |
| `repositories.py` | All SQL, parameterized through SQLAlchemy Core; returns plain dicts |
| `models.py` | `authors` and `books` `Table` definitions with constraints (also Alembic's metadata) |
| `database.py` | Async engine and `get_connection` dependency |
| `config.py` | `Settings` read from environment / `.env` |
| `migrations/` | Alembic environment and versioned migrations |

### 2.3 Layering

```mermaid
flowchart LR
    Request["HTTP request"] --> Route["Route (api.py)"]
    Route --> In["Create/Update model<br/>(validation)"]
    In --> Repo["Repository function"]
    Repo --> SQL["SQLAlchemy Core statement"]
    SQL --> DB[("PostgreSQL")]
    DB --> Row["Row mapping (dict)"]
    Row --> Out["Response model<br/>(response_model)"]
    Out --> Response["JSON response"]
```

---

## 3. Data design

### 3.1 Entity relationship

```mermaid
erDiagram
    AUTHORS ||--o{ BOOKS : writes

    AUTHORS {
        int id PK
        varchar name "NOT NULL, non-blank"
        varchar country "NULL"
    }

    BOOKS {
        int id PK
        varchar title "NOT NULL, non-blank"
        int year "NULL, > 0"
        numeric price "NUMERIC(12,2), >= 0"
        int author_id FK "NOT NULL, ON DELETE RESTRICT"
    }
```

### 3.2 Constraints

| Table | Constraint | Rule |
|---|---|---|
| `authors` | `ck_authors_name_nonempty` | `length(trim(name)) > 0` |
| `books` | `ck_books_title_nonempty` | `length(trim(title)) > 0` |
| `books` | `ck_books_year_positive` | `year IS NULL OR year > 0` |
| `books` | `ck_books_price_nonnegative` | `price >= 0` |
| `books` | `books_author_id_fkey` | `author_id -> authors.id ON DELETE RESTRICT` |

### 3.3 Pydantic models

```mermaid
classDiagram
    class AuthorCreate {
        +str name
        +str country
    }
    class AuthorUpdate {
        +str name
        +str country
    }
    class AuthorResponse {
        +int id
        +str name
        +str country
    }
    class BookCreate {
        +str title
        +int year
        +Decimal price
        +int author_id
    }
    class BookUpdate {
        +str title
        +int year
        +Decimal price
        +int author_id
    }
    class BookResponse {
        +int id
        +str title
        +int year
        +Decimal price
        +int author_id
    }
    class BookSummary {
        +int id
        +str title
        +str author
        +Decimal price
    }
```

`name` and `title` are stripped and non-empty. `country` and `year` are nullable; they are optional in the Create models and required (but nullable) in the Update models. `year` must be greater than 0, `price` must be at least 0 with at most 2 decimals, and `author_id` must be greater than 0.

### 3.4 Sample data (migration `0002_sample_data`)

| Author id | Name | Country |
|---:|---|---|
| 1 | J. R. R. Tolkien | United Kingdom |
| 2 | Ursula K. Le Guin | United States |
| 3 | George Orwell | United Kingdom |

| Book id | Title | Year | Price | Author id |
|---:|---|---:|---:|---:|
| 1 | The Hobbit | 1937 | 12.99 | 1 |
| 2 | The Fellowship of the Ring | 1954 | 14.99 | 1 |
| 3 | A Wizard of Earthsea | 1968 | 10.99 | 2 |
| 4 | The Left Hand of Darkness | 1969 | 11.50 | 2 |
| 5 | Nineteen Eighty-Four | 1949 | 9.99 | 3 |

---

## 4. Behavior design

### 4.1 Transaction model

`get_connection` opens `engine.begin()` per request, so every request runs in a single transaction. It commits when the route returns and rolls back if an exception escapes (including `HTTPException`).

### 4.2 Create book

```mermaid
sequenceDiagram
    actor Client
    participant API as FastAPI route
    participant Val as Pydantic BookCreate
    participant Repo as repositories.create_book
    participant DB as PostgreSQL

    Client->>API: POST /api/books
    API->>Val: Validate body
    alt Invalid body
        Val-->>Client: 422 Unprocessable Entity
    else Valid
        API->>Repo: create_book(connection, book)
        Repo->>DB: SELECT id FROM authors WHERE id = :id
        alt Author missing
            Repo-->>API: None
            API-->>Client: 404 Author not found
        else Author exists
            Repo->>DB: INSERT INTO books ... RETURNING *
            DB-->>Repo: Row
            Repo-->>API: dict
            API-->>Client: 201 BookResponse
        end
    end
```

### 4.3 Delete author

```mermaid
sequenceDiagram
    actor Client
    participant API as FastAPI route
    participant Repo as repositories.delete_author
    participant DB as PostgreSQL

    Client->>API: DELETE /api/authors/{id}
    API->>Repo: delete_author(connection, id)
    Repo->>DB: SELECT id FROM authors WHERE id = :id FOR UPDATE
    alt Not found
        Repo-->>API: missing
        API-->>Client: 404
    else Found
        Repo->>DB: SELECT id FROM books WHERE author_id = :id LIMIT 1
        alt Has books
            Repo-->>API: conflict
            API-->>Client: 409 Conflict
        else No books
            Repo->>DB: DELETE FROM authors WHERE id = :id
            Repo-->>API: deleted
            API-->>Client: 204 No Content
        end
    end
```

`FOR UPDATE` serializes concurrent deletes of the same author; the `RESTRICT` foreign key remains the final guard.

### 4.4 Book summary projection

```mermaid
sequenceDiagram
    actor Client
    participant API as FastAPI route
    participant Repo as repositories.list_book_summaries
    participant DB as PostgreSQL

    Client->>API: GET /api/books/summary
    API->>Repo: list_book_summaries(connection)
    Repo->>DB: SELECT b.id, b.title, a.name AS author, b.price FROM books b JOIN authors a ON a.id = b.author_id ORDER BY b.id
    DB-->>Repo: Projected rows
    Repo-->>API: list of dicts
    API-->>Client: 200 list of BookSummary
```

The route `/api/books/summary` is declared before `/api/books/{book_id}` so it is not captured as an ID.

### 4.5 Status code decision flow

```mermaid
flowchart TD
    Req["Request"] --> Valid{"Body / path valid?"}
    Valid -->|No| E422["422"]
    Valid -->|Yes| Found{"Target resource exists?"}
    Found -->|No| E404["404"]
    Found -->|Yes| Ref{"Referenced author exists?<br/>(book create/update)"}
    Ref -->|No| E404b["404 Author not found"]
    Ref -->|Yes| Rel{"Author delete with books?"}
    Rel -->|Yes| E409["409"]
    Rel -->|No| Ok["200 / 201 / 204"]
```

### 4.6 Frontend flow

```mermaid
flowchart TD
    Load["Page load"] --> Fetch["GET /api/books/summary + GET /api/authors"]
    Fetch --> Render["Render books and authors tables"]
    Render --> Add["Add / Edit form"]
    Render --> Del["Delete (confirm dialog)"]
    Add -->|"POST / PUT"| Api["REST API"]
    Del -->|"DELETE"| Api
    Api -->|"2xx"| Fetch
    Api -->|"4xx"| Msg["Show error message<br/>(422 details, 404, 409)"]
    Msg --> Render
```

`Add a book` is disabled until at least one author exists.

---

## 5. Database migrations

### 5.1 Revision chain

```mermaid
flowchart LR
    Base(["base"]) --> R1["0001_catalog<br/>authors + books + constraints"]
    R1 --> R2["0002_sample_data<br/>3 authors, 5 books, sequence reset"]
    R2 --> Head(["head"])
```

### 5.2 Migration workflow

```mermaid
flowchart TD
    Change["Edit models.py"] --> Gen["alembic revision --autogenerate -m message"]
    Gen --> Review["Review generated file"]
    Review --> Up["alembic upgrade head"]
    Up --> Check["alembic check (no drift)"]
    Up -.->|"problem"| Down["alembic downgrade -1"]
```

| Task | Command |
|---|---|
| Apply all migrations | `uv run alembic upgrade head` |
| Roll back one | `uv run alembic downgrade -1` |
| Show history | `uv run alembic history` |
| Detect drift | `uv run alembic check` |
| Adopt a database created before migrations | `uv run alembic stamp 0001_catalog` then `uv run alembic upgrade head` |

---

## 6. Deployment (local development)

```mermaid
flowchart LR
    Dev["Developer"] --> UV["uv run uvicorn<br/>127.0.0.1:8000"]
    Dev --> Compose["docker compose up -d"]
    Compose --> PG[("postgres:17<br/>localhost:5432<br/>db: book_catalog")]
    UV -->|"DATABASE_URL<br/>postgresql+asyncpg"| PG
    Dev --> Alem["uv run alembic upgrade head"] --> PG
    Dev --> Pytest["uv run pytest"] --> PG
```

### 6.1 Configuration

| Setting | Source | Default |
|---|---|---|
| `DATABASE_URL` | `.env` or environment | `postgresql+asyncpg://book_catalog:book_catalog@localhost:5432/book_catalog` |

---

## 7. API reference

Base URL: `http://127.0.0.1:8000`. Interactive documentation: `/docs`.

| Method | Path | Success | Errors |
|---|---|---|---|
| GET | `/api/books` | 200 | |
| GET | `/api/books/summary` | 200 | |
| GET | `/api/books/{id}` | 200 | 404, 422 |
| POST | `/api/books` | 201 | 404 (author), 422 |
| PUT | `/api/books/{id}` | 200 | 404 (book or author), 422 |
| DELETE | `/api/books/{id}` | 204 | 404 |
| GET | `/api/authors` | 200 | |
| GET | `/api/authors/{id}` | 200 | 404, 422 |
| POST | `/api/authors` | 201 | 422 |
| PUT | `/api/authors/{id}` | 200 | 404, 422 |
| DELETE | `/api/authors/{id}` | 204 | 404, 409 |

Error bodies: `{"detail": "Book not found"}` for 404/409, and FastAPI's standard `detail` array for 422.

### 7.1 Sample calls: curl

Use `curl.exe` in Windows PowerShell (plain `curl` is an alias for `Invoke-WebRequest`). Quoting JSON inline is awkward in PowerShell, so use the samples in 7.2 there.

```bash
# List books
curl http://127.0.0.1:8000/api/books

# Book summary projection
curl http://127.0.0.1:8000/api/books/summary

# Get one book
curl http://127.0.0.1:8000/api/books/1

# Create an author
curl -X POST http://127.0.0.1:8000/api/authors \
  -H "Content-Type: application/json" \
  -d '{"name": "Terry Pratchett", "country": "United Kingdom"}'

# Create a book (use the author id returned above)
curl -X POST http://127.0.0.1:8000/api/books \
  -H "Content-Type: application/json" \
  -d '{"title": "Guards! Guards!", "year": 1989, "price": "9.50", "author_id": 4}'

# Replace a book (all fields required)
curl -X PUT http://127.0.0.1:8000/api/books/6 \
  -H "Content-Type: application/json" \
  -d '{"title": "Guards! Guards!", "year": null, "price": "10.00", "author_id": 4}'

# Replace an author
curl -X PUT http://127.0.0.1:8000/api/authors/4 \
  -H "Content-Type: application/json" \
  -d '{"name": "Sir Terry Pratchett", "country": null}'

# Delete a book, then an author
curl -X DELETE http://127.0.0.1:8000/api/books/6 -i
curl -X DELETE http://127.0.0.1:8000/api/authors/4 -i
```

### 7.2 Sample calls: PowerShell

```powershell
$base = "http://127.0.0.1:8000"

Invoke-RestMethod "$base/api/books/summary"

$author = Invoke-RestMethod -Method Post -Uri "$base/api/authors" `
  -ContentType "application/json" `
  -Body (@{ name = "Terry Pratchett"; country = "United Kingdom" } | ConvertTo-Json)

$book = Invoke-RestMethod -Method Post -Uri "$base/api/books" `
  -ContentType "application/json" `
  -Body (@{ title = "Guards! Guards!"; year = 1989; price = "9.50"; author_id = $author.id } | ConvertTo-Json)

Invoke-RestMethod -Method Put -Uri "$base/api/books/$($book.id)" `
  -ContentType "application/json" `
  -Body (@{ title = "Guards! Guards!"; year = $null; price = "10.00"; author_id = $author.id } | ConvertTo-Json)

Invoke-RestMethod -Method Delete -Uri "$base/api/books/$($book.id)"
Invoke-RestMethod -Method Delete -Uri "$base/api/authors/$($author.id)"
```

### 7.3 Sample responses

Generated IDs (`4`, `6`) assume a freshly migrated database; on a database that has already created and deleted rows, they will be higher.

`GET /api/books/summary` -> `200`

```json
[
  { "id": 1, "title": "The Hobbit", "author": "J. R. R. Tolkien", "price": "12.99" },
  { "id": 2, "title": "The Fellowship of the Ring", "author": "J. R. R. Tolkien", "price": "14.99" }
]
```

`POST /api/authors` -> `201`

```json
{ "id": 4, "name": "Terry Pratchett", "country": "United Kingdom" }
```

`POST /api/books` -> `201`

```json
{ "id": 6, "title": "Guards! Guards!", "year": 1989, "price": "9.50", "author_id": 4 }
```

### 7.4 Sample error cases

| Call | Result |
|---|---|
| `GET /api/books/999999` | `404` `{"detail": "Book not found"}` |
| `POST /api/books` with `"author_id": 999999` | `404` `{"detail": "Author not found"}` |
| `POST /api/authors` with `{"name": "   "}` | `422` validation detail |
| `POST /api/books` with `"price": "-1.00"` | `422` validation detail |
| `PUT /api/authors/4` with `{"name": "X"}` (missing `country`) | `422` validation detail |
| `DELETE /api/authors/1` (has books) | `409` `{"detail": "Cannot delete an author with associated books"}` |

```bash
curl -i -X DELETE http://127.0.0.1:8000/api/authors/1
```

```text
HTTP/1.1 409 Conflict
{"detail":"Cannot delete an author with associated books"}
```

---

## 8. Testing design

```mermaid
flowchart TB
    Pytest["pytest + pytest-asyncio"] --> Fixture["client fixture"]
    Fixture --> Mig["alembic upgrade head"]
    Fixture --> Asgi["httpx AsyncClient + ASGITransport"]
    Asgi --> App["FastAPI app"] --> PG[("PostgreSQL")]
```

| Test | Covers |
|---|---|
| `test_book_and_author_crud_and_summary` | CRUD for both entities, summary projection, author-delete `409` |
| `test_request_validation_and_missing_resources` | `422` validation, `404` responses, frontend and static assets served |
| `test_sample_catalog_is_available` | Migration sample data |

Run with `uv run pytest` (PostgreSQL must be running).
