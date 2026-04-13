"""
Database connection and session management

PGBOUNCER FIX:
  Supabase uses pgbouncer in transaction pooling mode, which does NOT
  support prepared statements. asyncpg caches prepared statements by
  default, causing DuplicatePreparedStatementError on every request
  after the first.

  Fix: pass statement_cache_size=0 and prepared_statement_cache_size=0
  via the asyncpg connect_args. The SQLAlchemy-level compiled_cache
  must also be disabled. NullPool prevents connection reuse which would
  otherwise re-trigger the conflict.
"""
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from .config import settings


def _make_engine():
    """
    Build the async engine with all pgbouncer-safe settings.

    Key settings:
      - NullPool          : no connection pooling on our side
                            (pgbouncer handles it)
      - statement_cache_size=0          : asyncpg level — no prepared stmts
      - prepared_statement_cache_size=0 : asyncpg level (redundant but safe)
      - prepared_statement_name_func    : makes every statement name unique
                                          so there's never a collision even
                                          if the cache somehow fires
      - jit=off           : Supabase/pgbouncer edge-case stability
    """
    connect_args = {
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
        # Give every prepared statement a globally unique name so that
        # even if pgbouncer leaks one across a connection, it won't
        # collide with the next request's statement.
        "prepared_statement_name_func": lambda: f"__sentinel_{id(object())}__",
        "server_settings": {
            "jit": "off",
            "application_name": "sentinel_backend",
        },
    }

    return create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        future=True,
        # NullPool = a new connection per request; pgbouncer pools them
        # externally. This avoids the "already exists" clash that happens
        # when SQLAlchemy reuses a connection whose prepared-statement
        # cache is out of sync with pgbouncer's view.
        poolclass=NullPool,
        connect_args=connect_args,
        # Disable SQLAlchemy's own compiled query cache — it can emit the
        # same prepared-statement name on different connections.
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