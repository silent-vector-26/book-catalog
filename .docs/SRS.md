# Software Requirements Specification
## Book Catalog

**Version:** 0.1  
**Status:** Draft  
**License:** MIT

---

## 1. Introduction

### 1.1 Purpose

Book Catalog is a small full-stack application intended to evaluate modern Python application development.

The project will demonstrate:

- Web application development with Python
- REST API development
- Asynchronous programming
- PostgreSQL database access
- CRUD operations
- SQL projections and joins
- Request and response validation
- Typed application models
- Automated testing
- Python dependency and environment management

The application is intended for research and learning rather than production use.

### 1.2 Scope

Book Catalog manages information about books and their authors.

The system provides:

- A simple web frontend
- A REST API
- Book CRUD operations
- Author CRUD operations
- Book and author relationships
- Data projections combining information from multiple entities
- Persistent storage in PostgreSQL

### 1.3 Technology Stack

| Area | Technology |
|---|---|
| Language | Python |
| Web/API framework | FastAPI |
| Validation / DTOs | Pydantic |
| Database access | SQLAlchemy Core |
| PostgreSQL driver | asyncpg |
| Database | PostgreSQL |
| Templates | Jinja2 |
| Testing | pytest |
| Dependency management | uv |
| Local infrastructure | Docker Compose |

---

## 2. System Overview

```mermaid
flowchart TB
    Browser["Web Browser"]
    UI["Web Frontend<br/>HTML / Jinja2 / JavaScript"]
    API["FastAPI API<br/>Pydantic Models<br/>Application Logic<br/>Repositories"]
    DBAccess["SQLAlchemy Core<br/>asyncpg"]
    DB[("PostgreSQL")]

    Browser --> UI
    UI -->|HTTP| API
    API -->|Async database access| DBAccess
    DBAccess --> DB
```

### 2.1 Request Flow

```mermaid
sequenceDiagram
    actor User
    participant Web as Web Frontend
    participant API as FastAPI
    participant Validation as Pydantic
    participant Repo as Repository
    participant DB as PostgreSQL

    User->>Web: Perform action
    Web->>API: HTTP request
    API->>Validation: Validate request

    alt Valid request
        Validation-->>API: Validated model
        API->>Repo: Execute operation
        Repo->>DB: Async SQL query
        DB-->>Repo: Query result
        Repo-->>API: Typed result
        API-->>Web: HTTP response
        Web-->>User: Updated view
    else Invalid request
        Validation-->>API: Validation error
        API-->>Web: Error response
        Web-->>User: Validation feedback
    end
```

---

## 3. Data Model

### 3.1 Author

| Field | Type | Required | Description |
|---|---|---:|---|
| `id` | integer | Yes | Unique identifier |
| `name` | string | Yes | Author name |
| `country` | string | No | Author's country |

### 3.2 Book

| Field | Type | Required | Description |
|---|---|---:|---|
| `id` | integer | Yes | Unique identifier |
| `title` | string | Yes | Book title |
| `year` | integer | No | Publication year |
| `price` | decimal | Yes | Book price |
| `author_id` | integer | Yes | Associated author |

### 3.3 Relationships

```mermaid
erDiagram
    AUTHOR ||--o{ BOOK : writes

    AUTHOR {
        int id PK
        string name
        string country
    }

    BOOK {
        int id PK
        string title
        int year
        decimal price
        int author_id FK
    }
```

---

## 4. Functional Requirements

### FR-001: List Books

`GET /api/books`

The system shall allow a user to retrieve the list of books.

### FR-002: Get Book

`GET /api/books/{id}`

The system shall allow a user to retrieve a specific book by its identifier. If no book exists, the API shall return a not-found response.

### FR-003: Create Book

`POST /api/books`

The system shall validate the input before inserting the book.

```json
{
  "title": "The Hobbit",
  "year": 1937,
  "price": "12.99",
  "author_id": 1
}
```

### FR-004: Update Book

`PUT /api/books/{id}`

The system shall validate the complete replacement representation before
persisting changes. All editable fields are required.

### FR-005: Delete Book

`DELETE /api/books/{id}`

After successful deletion, the book shall no longer be returned by book queries.

### FR-006: List Authors

`GET /api/authors`

### FR-007: Get Author

`GET /api/authors/{id}`

### FR-008: Create Author

`POST /api/authors`

```json
{
  "name": "J. R. R. Tolkien",
  "country": "United Kingdom"
}
```

### FR-009: Update Author

`PUT /api/authors/{id}`

The system shall validate the complete replacement representation before
persisting changes. All editable fields are required.

### FR-010: Delete Author

`DELETE /api/authors/{id}`

The implementation shall handle attempts to delete authors that still have associated books.
Such requests shall be rejected with `409 Conflict`; associated books shall
not be deleted automatically.

---

## 5. Projection Requirements

### FR-011: Book Summary Projection

`GET /api/books/summary`

The projection shall contain book identifier, title, author name, and price.

```json
[
  {
    "id": 101,
    "title": "The Hobbit",
    "author": "J. R. R. Tolkien",
    "price": "12.99"
  }
]
```

The projection should be performed by the database query rather than by loading complete Book and Author objects into application memory.

```sql
SELECT
    b.id,
    b.title,
    a.name AS author,
    b.price
FROM books b
JOIN authors a ON a.id = b.author_id;
```

The result shall be mapped to a dedicated Pydantic response model.
Prices shall be represented in JSON as decimal strings to avoid floating-point
rounding.

### 5.2 List Behavior

Book and author list endpoints shall return JSON arrays, ordered by ascending
identifier. Initial list endpoints do not require pagination.

### 5.1 Projection Flow

```mermaid
flowchart LR
    Request["GET /api/books/summary"] --> API["FastAPI"]
    API --> Repo["Book Repository"]
    Repo --> Query["SQL JOIN + Projection"]
    Book[("Book")] --> Query
    Author[("Author")] --> Query
    Query --> Model["BookSummary<br/>Pydantic Model"]
    Model --> API
    API --> Response["JSON Response"]
```

---

## 6. Validation Requirements

### FR-012: Request Validation

The API shall use typed Pydantic models for request validation. Validation shall include required fields, expected data types, price validity, and publication year validity where supplied.

Author names and book titles shall not be empty or whitespace-only. Book prices
shall be non-negative fixed-precision decimal values. A publication year may be
omitted; when supplied, it shall be a positive integer.

### FR-013: Response Models

Database records shall not define the public API contract directly. Separate models may include:

- `BookCreate`
- `BookUpdate`
- `BookResponse`
- `BookSummary`
- `AuthorCreate`
- `AuthorUpdate`
- `AuthorResponse`

```mermaid
flowchart LR
    Request["HTTP Request"] --> Input["Create / Update<br/>Pydantic Model"]
    Input --> API["API / Application Logic"]
    API --> Repo["Repository"]
    Repo --> DB[("PostgreSQL")]
    DB --> Repo
    Repo --> Output["Response / Projection<br/>Pydantic Model"]
    Output --> Response["HTTP Response"]
```

---

## 7. Database Requirements

### DB-001: PostgreSQL
Application data shall be persisted in PostgreSQL.

### DB-002: Asynchronous Access
Database operations shall use asynchronous database access.

### DB-003: Parameterized Queries
Values supplied by clients shall use query parameters rather than direct string interpolation.

```sql
SELECT id, title, price
FROM books
WHERE id = :id;
```

### DB-004: Relationships
The database shall maintain the relationship between books and authors using a foreign key.

### DB-005: Transactions
Operations requiring multiple related database modifications shall execute within a transaction. The demo should include at least one operation or test demonstrating transaction behavior.

### DB-006: Schema Migrations and Sample Data
Database schema changes shall be managed through Alembic migrations. A new
database shall receive the authors and books schema and a small sample catalog
when upgraded to the latest migration. Starting the application shall not
silently create or modify the schema.

### 7.1 Database Access Architecture

```mermaid
flowchart TB
    API["FastAPI Endpoint"] --> Model["Pydantic Model"]
    API --> Repo["Repository"]
    Repo --> SA["SQLAlchemy Core"]
    SA --> Driver["asyncpg"]
    Driver --> DB[("PostgreSQL")]
    DB --> Driver --> SA --> Repo --> Model --> API
```

---

## 8. Web Frontend Requirements

### UI-001: Book List
The frontend shall display title, author, price, edit, delete, and add-book actions.

### UI-002: Create Book
The frontend shall provide a form for creating a book.

### UI-003: Edit Book
The frontend shall allow an existing book to be edited.

### UI-004: Delete Book
The frontend shall allow the user to delete a book.

### UI-005: Author Management
The frontend shall provide basic author management capabilities.

### UI-006: Validation Feedback
Validation or API errors shall be communicated to the user.

### 8.1 User Interaction Flow

```mermaid
flowchart TD
    List["Book List"]
    List -->|Add Book| Create["Create Book Form"]
    List -->|Edit| Edit["Edit Book Form"]
    List -->|Delete| Delete["Delete Book"]
    Create -->|Save| API["REST API"]
    Edit -->|Save| API
    Delete -->|Confirm| API
    API -->|Success| List
    API -->|Validation Error| Error["Display Error"]
    Error --> Create
    Error --> Edit
```

---

## 9. API Error Handling

| Situation | Status |
|---|---:|
| Successful query | 200 |
| Successful creation | 201 |
| Successful deletion | 204 |
| Invalid request | 422 |
| Resource not found | 404 |
| Operation conflicts with existing relationships | 409 |
| Unexpected server error | 500 |

Request validation failures shall use FastAPI's standard `422 Unprocessable
Entity` response.

Internal implementation details, database connection strings, credentials, or stack traces shall not intentionally be exposed through API error responses.

### 9.1 Error Handling Flow

```mermaid
flowchart TD
    Request["HTTP Request"] --> Validate{"Request valid?"}
    Validate -->|No| ValidationError["Validation Error"] --> ClientError["4xx Response"]
    Validate -->|Yes| Execute["Execute Operation"] --> Exists{"Resource / operation valid?"}
    Exists -->|No| BusinessError["Not Found / Client Error"] --> ClientError
    Exists -->|Yes| Database["Database Operation"] --> Success{"Successful?"}
    Success -->|Yes| Response["2xx Response"]
    Success -->|No| ServerError["5xx Response"]
```

---

## 10. Configuration

Configuration shall be separate from application source code. Local configuration should use an `.env` file.

```dotenv
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/book_catalog
```

The repository shall provide `.env.example`. The real `.env` shall not be committed.

---

## 11. Testing Requirements

### TEST-001: Unit Tests
The project should contain unit tests for application logic where appropriate.

### TEST-002: API Tests
Tests should cover creating, retrieving, updating, and deleting a book; retrieving the summary projection; invalid input; and nonexistent resources.

### TEST-003: Database Integration
At least one test shall exercise the application against PostgreSQL.

### 11.1 Testing Scope

```mermaid
flowchart TB
    Tests["pytest"] --> Unit["Unit Tests"]
    Tests --> API["API Tests"]
    Tests --> Integration["Integration Tests"]
    Unit --> Logic["Application Logic"]
    API --> FastAPI["FastAPI Endpoints"]
    Integration --> App["Application"] --> TestDB[("PostgreSQL Test Database")]
```

---

## 12. Project Structure

```text
book-catalog/
├── src/
│   └── book_catalog/
│       ├── __init__.py
│       ├── main.py
│       ├── api.py
│       ├── config.py
│       ├── database.py
│       ├── models.py
│       ├── repositories.py
│       ├── schemas.py
│       ├── migrations/
│       │   ├── env.py
│       │   └── versions/
│       ├── static/
│       │   ├── app.js
│       │   └── styles.css
│       └── templates/
│           └── index.html
├── alembic.ini
├── tests/
│   └── test_api.py
├── .env.example
├── .gitignore
├── compose.yaml
├── pyproject.toml
├── uv.lock
├── README.md
└── LICENSE
```

---

## 13. Development Requirements

### DEV-001: Dependency Management
The project shall use `uv`.

### DEV-002: Dependency Declaration
Dependencies shall be declared in `pyproject.toml` and resolved dependencies recorded in `uv.lock`.

### DEV-003: Local Database
PostgreSQL should be runnable locally using Docker Compose.

### DEV-004: Source Control
Generated files, virtual environments, local configuration, and development caches shall not be committed.

### 13.1 Local Development Environment

```mermaid
flowchart LR
    Developer["Developer"] --> UV["uv"] --> App["Book Catalog"]
    Developer --> Docker["Docker Compose"] --> DB[("PostgreSQL")]
    App -->|Async SQL| DB
```

---

## 14. Non-Functional Requirements

### NFR-001: Simplicity
The implementation should prioritize readability and learning value over architectural complexity.

### NFR-002: Type Safety
Python type annotations should be used throughout the application where practical.

### NFR-003: Asynchronous I/O
I/O-bound HTTP and database operations should use Python asynchronous programming patterns.

### NFR-004: Maintainability
Database access, API handling, and application models should remain reasonably separated.

### NFR-005: Security
Database credentials shall not be stored in source control. SQL containing user-controlled values shall use parameters.

---

## 15. Out of Scope

The initial version does not require:

- Authentication or authorization
- User accounts or role management
- Payment processing
- Cloud deployment
- Production-grade monitoring
- High availability
- Distributed architecture or microservices
- Advanced frontend frameworks
- Production-level security hardening

---

## 16. Research Objectives

The implementation should provide enough functionality to evaluate:

1. Python `async` / `await` compared with C#
2. FastAPI compared with ASP.NET Core
3. Pydantic compared with C# DTOs and records
4. SQLAlchemy Core compared with Dapper
5. Python type hints and IDE tooling
6. Dependency management with uv
7. pytest for unit and integration testing
8. PostgreSQL transactions
9. Python debugging
10. Containerized development

### 16.1 Research Areas

```mermaid
mindmap
  root((Python Research))
    Web
      FastAPI
      REST API
      Jinja2
    Language
      Type hints
      Async await
      Debugging
    Data
      PostgreSQL
      SQLAlchemy Core
      asyncpg
      Transactions
      Projections
    Models
      Pydantic
      Validation
      DTOs
    Development
      uv
      pytest
      Docker Compose
```

---

## 17. Acceptance Criteria

The initial research implementation shall be considered complete when:

- The application starts locally.
- PostgreSQL runs locally through Docker Compose.
- Authors can be created, read, updated, and deleted.
- Books can be created, read, updated, and deleted.
- Books are associated with authors.
- API requests and responses use Pydantic models.
- Database access is asynchronous.
- CRUD operations persist data in PostgreSQL.
- A joined Book Summary projection is available.
- A simple browser-based frontend supports the primary CRUD workflow.
- Representative automated tests execute successfully.
- Project dependencies can be restored using `uv sync`.

### 17.1 Completion Overview

```mermaid
flowchart LR
    Start["Research Demo"] --> CRUD["Author & Book CRUD"]
    CRUD --> Validation["Pydantic Validation"]
    Validation --> Async["Async Database Access"]
    Async --> Projection["Joined Projection"]
    Projection --> UI["Web Frontend"]
    UI --> Tests["Automated Tests"]
    Tests --> Complete(("Demo Complete"))
```

---

## 18. Summary

The Book Catalog application provides a deliberately small domain for evaluating the modern Python development ecosystem.

The project emphasizes:

- Explicit and understandable application structure
- Asynchronous programming
- Typed models and validation
- Explicit SQL and projections
- PostgreSQL persistence
- REST API design
- Simple full-stack functionality
- Automated testing
- Modern Python project management

The implementation should remain small enough to understand end-to-end while providing enough functionality to compare the Python development experience with equivalent approaches in other technology stacks.
