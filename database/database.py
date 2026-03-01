import logging
from typing import Any

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, delete

from . import model

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, url: str, pool_size: int = 5, max_overflow: int = 10):
        self._engine = create_async_engine(
            url,
            pool_size=pool_size,
            max_overflow=max_overflow,
        )
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def database_init(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(model.Base.metadata.create_all)

    async def close(self) -> None:
        """Dispose of the connection pool."""
        await self._engine.dispose()

    @staticmethod
    def _to_dict(obj: Any) -> dict:
        return {c.key: getattr(obj, c.key) for c in obj.__table__.columns}

    async def select(self, table_class, parameters: dict | None = None) -> list[dict] | bool:
        """Select multiple records from the database."""
        async with self._session_factory() as session:
            try:
                stmt = select(table_class)
                if parameters:
                    stmt = stmt.filter_by(**parameters)
                result = await session.execute(stmt)
                return [self._to_dict(r) for r in result.scalars().all()]
            except Exception as e:
                logger.error("Select error: %s", e)
                return False

    async def select_one(self, table_class, parameters: dict | None = None) -> dict | None | bool:
        """Select a single record from the database."""
        async with self._session_factory() as session:
            try:
                stmt = select(table_class)
                if parameters:
                    stmt = stmt.filter_by(**parameters)
                result = await session.execute(stmt)
                obj = result.scalars().first()
                return self._to_dict(obj) if obj else None
            except Exception as e:
                logger.error("Select_one error: %s", e)
                return False

    async def create(self, table_class, values: dict) -> bool:
        """Create a new record in the database."""
        async with self._session_factory() as session:
            try:
                session.add(table_class(**values))
                await session.commit()
                return True
            except Exception as e:
                await session.rollback()
                logger.error("Create error: %s", e)
                return False

    async def update(self, table_class, criteria: dict, values: dict) -> bool:
        """Update a record in the database."""
        async with self._session_factory() as session:
            try:
                stmt = select(table_class).filter_by(**criteria)
                result = await session.execute(stmt)
                obj = result.scalars().first()
                if not obj:
                    return False
                for k, v in values.items():
                    setattr(obj, k, v)
                await session.commit()
                return True
            except Exception as e:
                await session.rollback()
                logger.error("Update error: %s", e)
                return False

    async def delete(self, table_class, criteria: dict) -> bool:
        """Delete records matching criteria (single-query, no SELECT)."""
        async with self._session_factory() as session:
            try:
                stmt = delete(table_class).filter_by(**criteria)
                result = await session.execute(stmt)
                await session.commit()
                return result.rowcount > 0
            except Exception as e:
                await session.rollback()
                logger.error("Delete error: %s", e)
                return False

    async def delete_all(self, table_class, criteria: dict) -> int | bool:
        """Delete all records matching the criteria from the database."""
        async with self._session_factory() as session:
            try:
                stmt = delete(table_class).filter_by(**criteria)
                result = await session.execute(stmt)
                await session.commit()
                return result.rowcount
            except Exception as e:
                await session.rollback()
                logger.error("Delete_all error: %s", e)
                return False
