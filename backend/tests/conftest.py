"""
Shared test fixtures for FastAPI + SQLAlchemy 2.0 + asyncpg + pytest-asyncio.

Uses NullPool to prevent asyncpg "another operation in progress" errors.
Each test gets a transactional session with SAVEPOINT rollback for isolation.
"""

import uuid

import sqlalchemy
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import NullPool

from app.core.database import Base, get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.main import app as fastapi_app

# Import all models so Base.metadata knows about every table
import app.models  # noqa: F401

# Fake user returned by the auth override in all tests
_FAKE_USER = User(
    id=uuid.uuid4(),
    email="test@test.com",
    hashed_password="fake",
    full_name="Test User",
    company_name="TestCo",
    is_active=True,
)


TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5433/hackeurope_test"


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def engine():
    """Session-scoped engine with NullPool (fresh connection per checkout)."""
    eng = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    """
    Function-scoped session with nested transaction for isolation.

    Opens a connection, begins a transaction, then starts a SAVEPOINT.
    After the test, the outer transaction is rolled back — no data persists.
    """
    async with engine.connect() as connection:
        transaction = await connection.begin()

        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            autoflush=False,
        )

        nested = await connection.begin_nested()

        @sqlalchemy.event.listens_for(
            session.sync_session, "after_transaction_end"
        )
        def restart_savepoint(sync_session, sync_transaction):
            if connection.closed:
                return
            if not nested.is_active:
                connection.sync_connection.begin_nested()

        yield session

        await session.close()
        if transaction.is_active:
            await transaction.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    """HTTPX async test client. follow_redirects handles trailing-slash redirects."""

    async def _override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = _override_get_db
    fastapi_app.dependency_overrides[get_current_user] = lambda: _FAKE_USER
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        follow_redirects=True,
    ) as ac:
        yield ac
    fastapi_app.dependency_overrides.clear()
