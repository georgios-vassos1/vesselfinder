import asyncio
import logging
import math
from datetime import datetime, timezone

from curl_cffi.requests import AsyncSession

from tracker.marine.config import REQUEST_HEADERS

log = logging.getLogger(__name__)

_DEFAULT_ZOOM = 4
_MAX_CONCURRENT = 5
_REQUEST_DELAY = 0.2

# MarineTraffic does not serve tiles entirely above this latitude (Arctic).
_MAX_SERVED_LAT = 74.0


def _tile_min_lat(y: int, zoom: int) -> float:
    """Return the southern (minimum) latitude of a Web Mercator tile."""
    n = 2**zoom
    return math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n))))


def tile_urls(template: str, zoom: int) -> list[str]:
    n = 2**zoom
    return [
        template.format(z=zoom, x=x, y=y)
        for x in range(n)
        for y in range(n)
        if _tile_min_lat(y, zoom) <= _MAX_SERVED_LAT
    ]


def _cookie_header(cookies: list[dict]) -> str:
    return "; ".join(f"{c['name']}={c['value']}" for c in cookies)


async def _fetch_tile(session: AsyncSession, url: str, headers: dict) -> list[dict]:
    try:
        resp = await session.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and isinstance(data.get("data"), dict):
            return data["data"].get("rows") or []
        return []
    except Exception as exc:
        log.debug("Skipped %s: %s", url, exc)
        return []


async def fetch_all(
    tile_url_template: str,
    cookies: list[dict],
    zoom: int = _DEFAULT_ZOOM,
) -> list[dict]:
    urls = tile_urls(tile_url_template, zoom)
    headers = {**REQUEST_HEADERS, "Cookie": _cookie_header(cookies)}
    semaphore = asyncio.Semaphore(_MAX_CONCURRENT)
    captured_at = datetime.now(timezone.utc).isoformat()
    vessels_by_id: dict[str, dict] = {}

    async def bounded_fetch(session: AsyncSession, url: str) -> None:
        async with semaphore:
            rows = await _fetch_tile(session, url, headers)
            for row in rows:
                ship_id = row.get("SHIP_ID")
                if ship_id:
                    vessels_by_id[ship_id] = {**row, "captured_at": captured_at}
            await asyncio.sleep(_REQUEST_DELAY)

    log.info("Fetching %d tiles at zoom:%d", len(urls), zoom)
    async with AsyncSession(impersonate="chrome") as session:
        await asyncio.gather(*(bounded_fetch(session, url) for url in urls))

    return list(vessels_by_id.values())
