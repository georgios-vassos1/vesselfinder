import asyncio
import logging
import os
from datetime import datetime, timezone

import psycopg

from tracker.aviation.fetcher import fetch_all
from tracker.aviation.models import Aircraft
from tracker.aviation.storage import ensure_schema, insert_aircraft
from tracker.storage import connect, get_connection

log = logging.getLogger(__name__)

_INTERVAL = int(os.environ.get("SCRAPE_INTERVAL_MINUTES", "10")) * 60


async def _scrape_once(conn: psycopg.Connection) -> int:
    captured_at = datetime.now(timezone.utc)
    raw = await fetch_all()
    aircraft = [Aircraft.from_proto(r, captured_at) for r in raw]
    return insert_aircraft(conn, aircraft)


async def _run_loop() -> None:
    log.info("Starting aviation tracker — interval: %d min", _INTERVAL // 60)

    conn = connect()
    ensure_schema(conn)

    try:
        while True:
            started = datetime.now(timezone.utc)
            try:
                conn = get_connection(conn)
                count = await _scrape_once(conn)
                elapsed = (datetime.now(timezone.utc) - started).total_seconds()
                log.info("Run complete — %d aircraft inserted in %.1fs", count, elapsed)
            except Exception:
                log.exception("Run failed — will retry after interval")
            await asyncio.sleep(_INTERVAL)
    finally:
        conn.close()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    asyncio.run(_run_loop())
