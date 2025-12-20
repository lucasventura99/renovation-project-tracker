# app/db/session.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

# 1. Create the Async Engine
# echo=True prints SQL queries to the console (great for debugging)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True, 
    future=True
)

# 2. Create the Session Factory
# expire_on_commit=False is CRITICAL for async. 
# It prevents SQLAlchemy from trying to lazy-load data after the session closes.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# 3. Dependency for FastAPI
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # automatic commit could happen here, but better to be explicit in services
        finally:
            await session.close()