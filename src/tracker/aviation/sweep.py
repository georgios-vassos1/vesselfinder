from __future__ import annotations

import asyncio
import logging
import os

from tracker.aviation.aircraft_db import load as load_aircraft_db
from tracker.aviation.aircraft_db import save as save_aircraft_db
from tracker.aviation.enricher import enrich_ids
from tracker.aviation.fetcher import fetch_all

log = logging.getLogger(__name__)

_BATCH = int(os.environ.get("SWEEP_BATCH_SIZE", "50"))
_INTERVAL = int(os.environ.get("SWEEP_INTERVAL_SECONDS", "10"))
_MAX_CONCURRENT = 1
_REQUEST_DELAY = 1.5


async def _sweep_once(aircraft_db: dict) -> int:
    raw = await fetch_all()
    all_ids = [format(r.flight_id, "x") for r in raw if r.flight_id]
    unknown = [fid for fid in all_ids if fid not in aircraft_db][:_BATCH]

    if not unknown:
        log.info("No new flight IDs — db covers %d entries", len(aircraft_db))
        return 0

    total_unknown = sum(1 for fid in all_ids if fid not in aircraft_db)
    log.info("Enriching %d new flight IDs (%d total unknown)", len(unknown), total_unknown)
    new = await enrich_ids(unknown, max_concurrent=_MAX_CONCURRENT, request_delay=_REQUEST_DELAY)

    if new:
        save_aircraft_db(new)
        aircraft_db.update(new)
        log.info("Saved %d new entries — db now covers %d", len(new), len(aircraft_db))

    return len(new)


async def _run_sweep() -> None:
    log.info("Starting aircraft DB sweep — batch: %d, interval: %ds", _BATCH, _INTERVAL)
    aircraft_db = load_aircraft_db()
    log.info("Loaded %d existing entries from aircraft_db", len(aircraft_db))

    while True:
        try:
            await _sweep_once(aircraft_db)
        except Exception:
            log.exception("Sweep cycle failed — retrying after interval")
        await asyncio.sleep(_INTERVAL)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    asyncio.run(_run_sweep())
