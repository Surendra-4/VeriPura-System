from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.async_database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    connect_args=settings.database_connect_args,
)

AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for SQLAlchemy async session.
    """
    async with AsyncSessionFactory() as session:
        yield session


async def verify_database_connection() -> None:
    """
    Fail fast if the configured database cannot be reached.
    """
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))


async def dispose_database_engine() -> None:
    """Dispose SQLAlchemy engine during app shutdown."""
    await engine.dispose()
