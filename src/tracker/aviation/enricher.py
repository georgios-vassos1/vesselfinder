from __future__ import annotations

import asyncio
import logging

from curl_cffi.requests import AsyncSession

from tracker.aviation.config import REQUEST_HEADERS

log = logging.getLogger(__name__)

_CLICKHANDLER = "https://data-live.flightradar24.com/clickhandler/?flight={}"
_MAX_CONCURRENT = 5
_REQUEST_DELAY = 0.3

_HEADERS = {
    "User-Agent": REQUEST_HEADERS["User-Agent"],
    "Referer": REQUEST_HEADERS["Referer"],
    "Accept": "application/json",
}


def _parse_clickhandler(data: dict) -> tuple[str | None, str | None, str | None]:
    ac = data.get("aircraft") or {}
    model = ac.get("model") or {}
    return (
        model.get("code") or None,
        ac.get("registration") or None,
        (ac.get("hex") or "").upper() or None,
    )


async def _fetch_one(
    session: AsyncSession,
    semaphore: asyncio.Semaphore,
    flight_id: str,
    request_delay: float = _REQUEST_DELAY,
) -> tuple[str, str | None, str | None, str | None] | None:
    async with semaphore:
        try:
            resp = await session.get(_CLICKHANDLER.format(flight_id), headers=_HEADERS)
            resp.raise_for_status()
            at, reg, icao = _parse_clickhandler(resp.json())
            return flight_id, at, reg, icao
        except Exception as exc:
            log.debug("Enrichment failed for %s: %s", flight_id, exc)
            return None
        finally:
            await asyncio.sleep(request_delay)


async def enrich_ids(
    flight_ids: list[str],
    max_concurrent: int = _MAX_CONCURRENT,
    request_delay: float = _REQUEST_DELAY,
) -> dict[str, tuple[str | None, str | None, str | None]]:
    """Return dict mapping flight_id → (aircraft_type, registration, icao24) for successful lookups."""
    if not flight_ids:
        return {}

    semaphore = asyncio.Semaphore(max_concurrent)
    async with AsyncSession(impersonate="chrome") as session:
        results = await asyncio.gather(*(
            _fetch_one(session, semaphore, fid, request_delay) for fid in flight_ids
        ))

    enrichment = {fid: (at, reg, icao) for r in results if r for fid, at, reg, icao in [r]}
    log.info("Enriched %d / %d flight IDs", len(enrichment), len(flight_ids))
    return enrichment
