"""Repositorios SQL contra PostgreSQL real. Se saltan si no hay TEST_DATABASE_URL.

TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/oncologico_test pytest -m integration
"""

import os
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.shared.infrastructure.orm_registry import Base

URL = os.environ.get("TEST_DATABASE_URL")

pytestmark = pytest.mark.integration


def pytest_collection_modifyitems(config, items):
    if URL:
        return
    skip = pytest.mark.skip(reason="TEST_DATABASE_URL no definida")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip)


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    assert URL and "test" in URL, "TEST_DATABASE_URL debe apuntar a una BD de pruebas (con 'test' en el nombre)"
    engine = create_async_engine(URL, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, expire_on_commit=False)() as s:
        yield s
    await engine.dispose()
