import logging

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from sqlalchemy import delete

from . import model

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, url):
        # Automatically switch to async driver if standard mysql/postgresql url is provided
        if url.startswith("mysql://"):
            url = url.replace("mysql://", "mysql+aiomysql://")
        elif url.startswith("postgresql://"):
             url = url.replace("postgresql://", "postgresql+asyncpg://")
        elif url.startswith("sqlite://") and "aiosqlite" not in url:
             url = url.replace("sqlite://", "sqlite+aiosqlite://")

        self.__engine = create_async_engine(url)
        self.__Session = sessionmaker(
            bind=self.__engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )

    async def database_init(self):
        if not self.__engine:
            raise Exception("Database is not connected.")
        async with self.__engine.begin() as conn:
            await conn.run_sync(model.Base.metadata.create_all)
        return True

    @staticmethod
    def _to_dict(obj):
        return {c.key: getattr(obj, c.key) for c in obj.__table__.columns}

    async def select(self, table_class, parameters=None):
        """Select multiple records from the database."""
        async with self.__Session() as session:
            try:
                stmt = select(table_class)
                if parameters:
                    stmt = stmt.filter_by(**parameters)
                result = await session.execute(stmt)
                results = result.scalars().all()
                return [self._to_dict(r) for r in results]
            except Exception as e:
                logger.error("Select error: %s", e)
                return False

    async def select_one(self, table_class, parameters=None):
        """Select a single record from the database."""
        async with self.__Session() as session:
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

    async def create(self, table_class, values):
        """Create a new record in the database."""
        async with self.__Session() as session:
            try:
                obj = table_class(**values)
                session.add(obj)
                await session.commit()
                return True
            except Exception as e:
                await session.rollback()
                logger.error("Create error: %s", e)
                return False

    async def update(self, table_class, criteria, values):
        """Update a record in the database."""
        async with self.__Session() as session:
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

    async def delete(self, table_class, criteria):
        """Delete a record from the database."""
        async with self.__Session() as session:
            try:
                stmt = select(table_class).filter_by(**criteria)
                result = await session.execute(stmt)
                obj = result.scalars().first()
                
                if not obj:
                    return False
                
                await session.delete(obj)
                await session.commit()
                return True
            except Exception as e:
                await session.rollback()
                logger.error("Delete error: %s", e)
                return False

    async def delete_all(self, table_class, criteria):
        """Delete all records matching the criteria from the database."""
        async with self.__Session() as session:
            try:
                stmt = delete(table_class).filter_by(**criteria)
                result = await session.execute(stmt)
                await session.commit()
                return result.rowcount
            except Exception as e:
                await session.rollback()
                logger.error("Delete_all error: %s", e)
                return False
