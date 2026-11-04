import asyncio

from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context
from app.shared.infrastructure.config import settings
from app.shared.infrastructure.orm_registry import Base

target_metadata = Base.metadata


def run_offline() -> None:
    context.configure(url=settings.database_url_async, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def _run(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


async def run_online() -> None:
    engine = create_async_engine(settings.database_url_async)
    async with engine.connect() as conn:
        await conn.run_sync(_run)
    await engine.dispose()


if context.is_offline_mode():
    run_offline()
else:
    asyncio.run(run_online())
