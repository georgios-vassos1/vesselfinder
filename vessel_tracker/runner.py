import asyncio
import logging
import os
from datetime import datetime, timezone

import psycopg

from vessel_tracker.ais_data_scraper import client
from vessel_tracker.models import Vessel
from vessel_tracker.storage import connect, ensure_schema, insert_vessels

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

_OS = os.environ.get("SCRAPE_OS", "Linux")
_INTERVAL = int(os.environ.get("SCRAPE_INTERVAL_MINUTES", "10")) * 60


def _get_connection(existing: psycopg.Connection | None) -> psycopg.Connection:
    """Return a live connection, reconnecting if the existing one is broken."""
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


async def _scrape_once(conn: psycopg.Connection) -> int:
    raw_vessels = await client(_OS)
    vessels = [Vessel.from_raw(r) for r in raw_vessels]
    return insert_vessels(conn, vessels)


async def _run_loop() -> None:
    log.info("Starting vessel tracker — OS: %s, interval: %d min", _OS, _INTERVAL // 60)

    conn = connect()
    ensure_schema(conn)

    try:
        while True:
            started = datetime.now(timezone.utc)
            try:
                conn = _get_connection(conn)
                count = await _scrape_once(conn)
                elapsed = (datetime.now(timezone.utc) - started).total_seconds()
                log.info("Run complete — %d vessels inserted in %.1fs", count, elapsed)
            except Exception:
                log.exception("Run failed — will retry after interval")
            await asyncio.sleep(_INTERVAL)
    finally:
        conn.close()


def main() -> None:
    asyncio.run(_run_loop())
