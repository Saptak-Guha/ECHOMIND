"""
EchoMind Database Connection
SQLAlchemy async engine and session management for PostgreSQL.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


async def get_db() -> AsyncSession:
    """Dependency that provides a database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Create all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def seed_demo_user():
    """Ensure the demo user referenced by the routes exists.

    Routes currently attribute all data to a fixed DEMO_USER_ID. Every domain
    table has a FK to users.id, so without this row any ingest fails with a
    foreign-key violation. Idempotent — safe to run on every startup.
    """
    from sqlalchemy import select
    from app.models.user import User
    from app.core.security import hash_password

    demo_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    async with async_session_factory() as session:
        existing = await session.execute(select(User).where(User.id == demo_id))
        if existing.scalar_one_or_none():
            return False
        session.add(
            User(
                id=demo_id,
                email="demo@echomind.local",
                username="demo",
                hashed_password=hash_password("demo"),
                full_name="Demo User",
            )
        )
        await session.commit()
        return True


async def close_db():
    """Close the database engine."""
    await engine.dispose()
