import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from infrastructure.database.models import Base


def create_database_engine(
    database_url: str,
    *,
    echo: bool = False,
    is_serverless: bool = False,
) -> AsyncEngine:
    """Create the async SQLAlchemy engine supporting SQLite and PostgreSQL (Supabase)."""
    # Normalize postgres URLs to use asyncpg driver
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql://") and not database_url.startswith("postgresql+"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # Automatically route Supabase direct IPv6 endpoints to IPv4 connection pooler
    if "db.qysrspvrpeobxnbnckgz.supabase.co" in database_url:
        database_url = database_url.replace(
            "db.qysrspvrpeobxnbnckgz.supabase.co",
            "aws-0-ap-southeast-1.pooler.supabase.com",
        )
        if "://postgres:" in database_url:
            database_url = database_url.replace("://postgres:", "://postgres.qysrspvrpeobxnbnckgz:", 1)

    engine_kwargs: dict[str, Any] = {
        "echo": echo,
        "future": True,
        "pool_pre_ping": True,
    }

    if "sqlite" in database_url:
        # Extract database path from URL and ensure parent directory exists
        clean_path = database_url.split(":///", 1)[-1]
        if clean_path and not clean_path.startswith(":memory:"):
            db_dir = Path(clean_path).parent
            if db_dir and not db_dir.exists():
                db_dir.mkdir(parents=True, exist_ok=True)
    elif "postgresql" in database_url:
        # Use NullPool in serverless environments (Vercel) to prevent connection leaks
        if is_serverless or os.getenv("VERCEL"):
            engine_kwargs["poolclass"] = NullPool
        if "pooler.supabase.com" in database_url or ":6543" in database_url:
            engine_kwargs["connect_args"] = {"statement_cache_size": 0}

    return create_async_engine(database_url, **engine_kwargs)




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
