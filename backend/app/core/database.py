from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.includes.models import BaseDBModel

production_database_engine = AsyncEngine(create_engine(str(settings.DATABASE_URI)))

DEVELOPMENT_DATABASE_URL = "sqlite:///testing.db"


async def initialize_database() -> None:
    """Creates all the tables in the database."""
    async with production_database_engine.begin() as conn:
        # await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(BaseDBModel.metadata.create_all)


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    """Provides a database session"""
    async_session = sessionmaker(  # type: ignore
        production_database_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        try:
            yield session
        except:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_session_ctx():
    async for session in get_db_session():
        yield session
