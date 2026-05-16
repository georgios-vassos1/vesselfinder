from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import replace
from datetime import datetime, timezone

import psycopg

from tracker.aviation.enricher import enrich_ids
from tracker.aviation.fetcher import fetch_all
from tracker.aviation.models import Aircraft
from tracker.aviation.opensky import load as load_opensky
from tracker.aviation.storage import ensure_schema, insert_aircraft, load_enrichment, store_enrichment
from tracker.storage import connect, get_connection

log = logging.getLogger(__name__)

_INTERVAL = int(os.environ.get("SCRAPE_INTERVAL_MINUTES", "10")) * 60
_ENRICH_BATCH = int(os.environ.get("ENRICH_BATCH_SIZE", "100"))


async def _scrape_once(
    conn: psycopg.Connection,
    opensky_db: dict[str, tuple[str | None, str | None]],
) -> int:
    captured_at = datetime.now(timezone.utc)
    raw = await fetch_all()
    aircraft = [Aircraft.from_proto(r, captured_at) for r in raw]

    all_ids = [a.flight_id for a in aircraft if a.flight_id]

    known = load_enrichment(conn, all_ids)

    new_ids = [fid for fid in all_ids if fid not in known][:_ENRICH_BATCH]
    new_enrichments = await enrich_ids(new_ids) if new_ids else {}

    if new_enrichments:
        store_enrichment(conn, {fid: icao for fid, (_, _, icao) in new_enrichments.items() if icao})
        log.info("Stored %d new icao24 mappings", len(new_enrichments))

    all_icao24 = {**known, **{fid: icao for fid, (_, _, icao) in new_enrichments.items() if icao}}

    def resolve(a: Aircraft) -> Aircraft:
        icao24 = all_icao24.get(a.flight_id)
        if not icao24:
            return a
        type_, reg = opensky_db.get(icao24, (None, None))
        return replace(a, icao24=icao24, aircraft_type=type_, registration=reg)

    return insert_aircraft(conn, [resolve(a) for a in aircraft])


async def _run_loop() -> None:
    log.info("Starting aviation tracker — interval: %d min", _INTERVAL // 60)

    conn = connect()
    ensure_schema(conn)
    opensky_db = load_opensky()
    log.info("Loaded %d aircraft from OpenSky DB", len(opensky_db))

    try:
        while True:
            started = datetime.now(timezone.utc)
            try:
                conn = get_connection(conn)
                count = await _scrape_once(conn, opensky_db)
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
