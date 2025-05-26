"""Application configuration module.

This module defines the AppConfig class, which loads application settings from
environment variables using Pydantic. It supports configurable paths for image
storage, logging, allowed file formats, and file size limits.

Side effects:
    - Reads and parses environment variables from the `.env` file during import.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory for resolving relative paths
BASE_DIR = Path(__file__).parent.parent.parent


class AppConfig(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        IMAGES_DIR (str): Directory path where uploaded images are stored.
        WEB_SERVER_WORKERS (int): Number of worker processes to run for the HTTP server.
        WEB_SERVER_START_PORT (int): Starting port number for worker processes.
        LOG_DIR (Path): Directory path where log files are saved.
        MAX_FILE_SIZE (int): Maximum allowed size of uploaded files (in bytes).
        SUPPORTED_FORMATS (set[str]): Set of allowed file extensions.
        POSTGRES_DB (str): Name of the PostgreSQL database to connect to.
        POSTGRES_DB_PORT (int): Port on which the PostgreSQL server is listening.
        POSTGRES_USER (str): Username for authenticating with PostgreSQL.
        POSTGRES_PASSWORD (str): Password for the PostgreSQL user.
        POSTGRES_HOST (str): Hostname or Docker service name of the PostgreSQL container.
        PGBOUNCER_USER (str): Username for PgBouncer authentication.
        PGBOUNCER_PASSWORD (str): Password for PgBouncer authentication.
        PGBOUNCER_HOST (str): Hostname or Docker service name of the PgBouncer container.
        PGBOUNCER_PORT (int): Port on which the PgBouncer server is listening.
        USE_PGBOUNCER (bool): Flag indicating whether to use PgBouncer for database connections.
    """


    IMAGES_DIR: str
    LOG_DIR: Path
    WEB_SERVER_WORKERS: int
    WEB_SERVER_START_PORT: int

    POSTGRES_DB: str
    POSTGRES_DB_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str

    PGBOUNCER_USER: str
    PGBOUNCER_PASSWORD: str
    PGBOUNCER_HOST: str
    PGBOUNCER_PORT: int
    USE_PGBOUNCER: bool = True

    MAX_FILE_SIZE: int = 1 * 1024 * 1024
    SUPPORTED_FORMATS: set[str] = {'.jpg', '.png', '.gif'}

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8"
    )

    @property
    def database_url(self) -> str:
        """Construct PostgreSQL connection string.

        Returns:
            str: Database connection URL in format suitable for psycopg.
        """
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_DB_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def pgbouncer_url(self) -> str:
        """Construct PgBouncer connection string.

        Returns:
            str: PgBouncer connection URL in format suitable for psycopg.
        """
        return (
            f"postgresql://{self.PGBOUNCER_USER}:{self.PGBOUNCER_PASSWORD}@"
            f"{self.PGBOUNCER_HOST}:{self.PGBOUNCER_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def db_url(self) -> str:
        """Return the active database connection URL.

        Uses PgBouncer if USE_PGBOUNCER is set to True, otherwise
        uses direct PostgreSQL connection.

        Returns:
            str: Active database connection URL.
        """
        return self.pgbouncer_url if self.USE_PGBOUNCER else self.database_url


config = AppConfig()
