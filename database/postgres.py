from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine


def create_postgres_engine(dsn: str) -> AsyncEngine:
    """Create a SQLAlchemy async engine for PostgreSQL.

    Pool settings are conservative for a sync pipeline that runs periodically.
    """
    return create_async_engine(
        dsn,
        pool_size=5,
        max_overflow=2,
        pool_pre_ping=True,
        echo=False,
    )
