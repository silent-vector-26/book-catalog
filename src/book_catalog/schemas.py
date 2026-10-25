from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class AuthorCreate(BaseModel):
    name: NonEmptyText
    country: str | None = None


class AuthorUpdate(BaseModel):
    name: NonEmptyText
    country: str | None


class AuthorResponse(BaseModel):
    id: int
    name: str
    country: str | None


class BookCreate(BaseModel):
    title: NonEmptyText
    year: int | None = Field(default=None, gt=0)
    price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    author_id: int = Field(gt=0)


class BookUpdate(BaseModel):
    title: NonEmptyText
    year: int | None = Field(gt=0)
    price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    author_id: int = Field(gt=0)


class BookResponse(BaseModel):
    id: int
    title: str
    year: int | None
    price: Decimal
    author_id: int


class BookSummary(BaseModel):
    id: int
    title: str
    author: str
    price: Decimal
