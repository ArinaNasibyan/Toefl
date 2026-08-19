from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from infrastructure.database.models import Base


def create_database_engine(database_url: str, *, echo: bool = False) -> AsyncEngine:
    """Create the async SQLAlchemy engine."""
    if "sqlite" in database_url:
        # Extract database path from URL and ensure parent directory exists
        clean_path = database_url.split(":///", 1)[-1]
        if clean_path and not clean_path.startswith(":memory:"):
            db_dir = Path(clean_path).parent
            if db_dir and not db_dir.exists():
                db_dir.mkdir(parents=True, exist_ok=True)

    return create_async_engine(
        database_url,
        echo=echo,
        future=True,
        pool_pre_ping=True,
    )



def create_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Create the async SQLAlchemy session factory."""

    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )


async def init_database(engine: AsyncEngine) -> None:
    """Create database tables for development startup."""

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def session_scope(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    session = session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
