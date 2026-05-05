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
