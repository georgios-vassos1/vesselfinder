import logging
import os

import psycopg
from psycopg.rows import dict_row

log = logging.getLogger(__name__)


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return url


def connect() -> psycopg.Connection:
    return psycopg.connect(_database_url(), row_factory=dict_row)


def get_connection(existing: psycopg.Connection | None) -> psycopg.Connection:
    """Return a live connection, reconnecting if the existing one has dropped."""
    if existing is not None:
        try:
            existing.execute("SELECT 1")
            return existing
        except Exception:
            log.warning("DB connection lost — reconnecting")
            try:
                existing.close()
            except Exception:
                pass
    return connect()
