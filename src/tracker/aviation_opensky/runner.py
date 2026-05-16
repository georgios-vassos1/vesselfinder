from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import psycopg

from tracker.aviation_opensky.auth import fetch_token
from tracker.aviation_opensky.fetcher import BoundingBox, fetch_states
from tracker.aviation_opensky.models import Aircraft
from tracker.aviation_opensky.storage import ensure_schema, insert_aircraft
from tracker.aviation.opensky import load as load_opensky
from tracker.storage import connect, get_connection

log = logging.getLogger(__name__)

_INTERVAL = int(os.environ.get("SCRAPE_INTERVAL_MINUTES", "10")) * 60
_TOKEN_REFRESH = 240  # seconds — refresh before 300s expiry

_DEFAULT_BBOX = BoundingBox(
    north=float(os.environ.get("BBOX_NORTH", "85")),
    south=float(os.environ.get("BBOX_SOUTH", "-85")),
    west=float(os.environ.get("BBOX_WEST", "-180")),
    east=float(os.environ.get("BBOX_EAST", "180")),
)


async def _scrape_once(
    conn: psycopg.Connection,
    opensky_db: dict[str, tuple[str | None, str | None]],
    bbox: BoundingBox = _DEFAULT_BBOX,
    token: str | None = None,
) -> int:
    captured_at = datetime.now(timezone.utc)
    raw = await fetch_states(bbox, token=token)
    aircraft = [Aircraft.from_raw(r, captured_at, opensky_db) for r in raw]
    return insert_aircraft(conn, aircraft)


async def _token_loop(client_id: str, client_secret: str, state: dict) -> None:
    while True:
        try:
            state["token"] = await fetch_token(client_id, client_secret)
            log.info("OpenSky token refreshed")
        except Exception:
            log.exception("Token refresh failed — continuing with existing token")
        await asyncio.sleep(_TOKEN_REFRESH)


async def _run_loop() -> None:
    log.info("Starting OpenSky tracker — interval: %d min", _INTERVAL // 60)

    conn = connect()
    ensure_schema(conn)
    db_path = os.environ.get("OPENSKY_DB_PATH")
    opensky_db = load_opensky(Path(db_path)) if db_path else load_opensky()
    log.info("Loaded %d aircraft from OpenSky DB", len(opensky_db))

    client_id = os.environ.get("OPENSKY_CLIENT_ID")
    client_secret = os.environ.get("OPENSKY_CLIENT_SECRET")

    token_state: dict[str, str | None] = {"token": None}
    if client_id and client_secret:
        asyncio.create_task(_token_loop(client_id, client_secret, token_state))
        await asyncio.sleep(2)  # allow first token fetch to complete

    try:
        while True:
            started = datetime.now(timezone.utc)
            try:
                conn = get_connection(conn)
                count = await _scrape_once(conn, opensky_db, token=token_state["token"])
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
