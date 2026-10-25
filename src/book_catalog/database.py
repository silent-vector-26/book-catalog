from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

from book_catalog.config import settings


def create_database_engine() -> AsyncEngine:
    return create_async_engine(settings.database_url, pool_pre_ping=True)


engine = create_database_engine()


async def get_connection() -> AsyncIterator[AsyncConnection]:
    async with engine.begin() as connection:
        yield connection
