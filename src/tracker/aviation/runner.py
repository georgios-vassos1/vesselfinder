from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import replace
from datetime import datetime, timezone

import psycopg

from tracker.aviation.aircraft_db import load as load_aircraft_db
from tracker.aviation.aircraft_db import save as save_aircraft_db
from tracker.aviation.enricher import enrich_ids
from tracker.aviation.fetcher import fetch_all
from tracker.aviation.models import Aircraft
from tracker.aviation.storage import ensure_schema, insert_aircraft, load_enrichment, store_enrichment
from tracker.storage import connect, get_connection

log = logging.getLogger(__name__)

_INTERVAL = int(os.environ.get("SCRAPE_INTERVAL_MINUTES", "10")) * 60
_ENRICH_BATCH = int(os.environ.get("ENRICH_BATCH_SIZE", "100"))


async def _scrape_once(conn: psycopg.Connection, aircraft_db: dict) -> int:
    captured_at = datetime.now(timezone.utc)
    raw = await fetch_all()
    aircraft = [Aircraft.from_proto(r, captured_at) for r in raw]

    all_ids = [a.flight_id for a in aircraft if a.flight_id]

    known = load_enrichment(conn, all_ids)
    db_hits = {fid: aircraft_db[fid] for fid in all_ids if fid not in known and fid in aircraft_db}

    new_ids = [fid for fid in all_ids if fid not in known and fid not in db_hits][:_ENRICH_BATCH]
    new_enrichments = await enrich_ids(new_ids) if new_ids else {}

    if new_enrichments:
        store_enrichment(conn, new_enrichments)
        save_aircraft_db(new_enrichments)
        aircraft_db.update(new_enrichments)
        log.info("Stored %d new enrichments", len(new_enrichments))

    all_enrichments = {**known, **db_hits, **new_enrichments}
    aircraft = [
        replace(a, aircraft_type=e[0], registration=e[1], icao24=e[2])
        if (e := all_enrichments.get(a.flight_id)) else a
        for a in aircraft
    ]

    return insert_aircraft(conn, aircraft)


async def _run_loop() -> None:
    log.info("Starting aviation tracker — interval: %d min", _INTERVAL // 60)

    conn = connect()
    ensure_schema(conn)
    aircraft_db = load_aircraft_db()
    log.info("Loaded %d entries from aircraft_db", len(aircraft_db))

    try:
        while True:
            started = datetime.now(timezone.utc)
            try:
                conn = get_connection(conn)
                count = await _scrape_once(conn, aircraft_db)
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
