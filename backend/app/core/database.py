"""
Database connection and session management

PGBOUNCER FIX:
  Supabase uses pgbouncer in transaction pooling mode, which does NOT
  support prepared statements. asyncpg caches prepared statements by
  default, causing DuplicatePreparedStatementError on every request
  after the first.

  Fix: statement_cache_size=0 disables asyncpg's cache. The name func
  uses UUID4 so names are unique across server restarts — a sequential
  counter would reset to 0 on hot-reload and collide with pgbouncer's
  cached names from the previous process.
"""
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from .config import settings
import uuid


def _make_engine():
    """
    Build the async engine with all pgbouncer-safe settings.

    Key settings:
      - NullPool                        : no pooling on our side
      - statement_cache_size=0          : asyncpg — no prepared stmts
      - prepared_statement_cache_size=0 : asyncpg (redundant but safe)
      - prepared_statement_name_func    : UUID per statement, unique across
                                          hot-reloads and parallel workers
      - jit=off                         : Supabase/pgbouncer stability
    """
    connect_args = {
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
        # UUID4 hex = 32 chars, globally unique, never collides with
        # pgbouncer's leftover names from a previous server process.
        "prepared_statement_name_func": lambda: f"__rs_{uuid.uuid4().hex}__",
        "server_settings": {
            "jit": "off",
            "application_name": "sentinel_backend",
        },
    }

    return create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        future=True,
        poolclass=NullPool,
        connect_args=connect_args,
        execution_options={"compiled_cache": None},
    )


engine = _make_engine()

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    FastAPI dependency — yields an async DB session.

    Usage:
        @router.get("/")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Create all tables (called at startup)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Dispose engine connections (called at shutdown)."""
    await engine.dispose()