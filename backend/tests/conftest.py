import os

import asyncpg
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import Base, get_session
from app.main import app


def _test_db_url() -> str:
    # Derive the test DB URL from DATABASE_URL by swapping the DB name
    # to "app_test". Fall back to a localhost URL so pytest works
    # outside Docker against a local Postgres.
    url = os.environ.get("DATABASE_URL", "postgresql+asyncpg://app:app@localhost:5432/app")
    base, _ = url.rsplit("/", 1)
    return f"{base}/app_test"


_TEST_DB_URL = _test_db_url()


async def _ensure_test_db_exists() -> None:
    # CREATE DATABASE cannot run inside a transaction, so we go around
    # SQLAlchemy and use asyncpg directly against the "postgres"
    # maintenance DB. Idempotent: only creates the DB if it isn't
    # there already.
    bare = _TEST_DB_URL.replace("+asyncpg", "")
    base, target = bare.rsplit("/", 1)
    conn = await asyncpg.connect(f"{base}/postgres")
    try:
        if not await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", target):
            await conn.execute(f'CREATE DATABASE "{target}"')
    finally:
        await conn.close()


@pytest_asyncio.fixture(scope="session")
async def async_engine():
    await _ensure_test_db_exists()
    engine = create_async_engine(_TEST_DB_URL)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def client(async_engine):
    # drop_all + create_all per test is ~50 ms on a local Postgres and
    # is the simplest correct isolation pattern when endpoints commit.
    # A SAVEPOINT-based fixture would be faster but harder to read.
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(async_engine, expire_on_commit=False)

    async def _override():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_session] = _override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
