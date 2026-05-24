from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Central config loaded from .env. Pydantic validates types at startup."""

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "kidshuttle"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"

    # SQLite
    sqlite_db_path: str = "database/manifest.db"

    # MinIO
    minio_endpoint: str = "http://localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "kidshuttle"

    # Paths
    excel_file_path: str = "drivers.xlsx"
    output_dir: str = "output"
    log_dir: str = "logs"

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    """Cached singleton — reads .env once per process."""
    return Settings()
