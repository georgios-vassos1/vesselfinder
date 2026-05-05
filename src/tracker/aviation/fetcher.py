import asyncio
import logging
import secrets
import string

from curl_cffi.requests import AsyncSession

from tracker.aviation.config import FR24_GRPC_URL, REQUEST_HEADERS
from tracker.aviation.proto import RawAircraftFields, decode_response, encode_request

log = logging.getLogger(__name__)

_MAX_CONCURRENT = 5
_REQUEST_DELAY = 0.2
_GRID_STEP = 20  # degrees — 162 cells covering the globe


def _bounds_cells() -> list[tuple[float, float, float, float]]:
    """Return (north, south, west, east) tuples for a 20°×20° global grid."""
    cells = []
    for lat_min in range(-90, 90, _GRID_STEP):
        for lon_min in range(-180, 180, _GRID_STEP):
            cells.append((
                float(lat_min + _GRID_STEP),
                float(lat_min),
                float(lon_min),
                float(lon_min + _GRID_STEP),
            ))
    return cells


def _device_id() -> str:
    chars = string.ascii_lowercase + string.digits
    short = "".join(secrets.choice(chars) for _ in range(8))
    long_ = "".join(secrets.choice(chars + "_-") for _ in range(22))
    return f"web-{short}-{long_}"


async def _fetch_cell(
    session: AsyncSession,
    bounds: tuple[float, float, float, float],
    headers: dict[str, str],
) -> list[RawAircraftFields]:
    north, south, west, east = bounds
    body = encode_request(north, south, west, east)
    try:
        resp = await session.post(FR24_GRPC_URL, data=body, headers=headers)
        resp.raise_for_status()
        return list(decode_response(resp.content))
    except Exception as exc:
        log.debug("Skipped cell %s: %s", bounds, exc)
        return []


async def fetch_all() -> list[RawAircraftFields]:
    cells = _bounds_cells()
    headers = {
        **REQUEST_HEADERS,
        "fr24-device-id": _device_id(),
    }
    semaphore = asyncio.Semaphore(_MAX_CONCURRENT)
    aircraft_by_id: dict[int, RawAircraftFields] = {}

    async def bounded_fetch(session: AsyncSession, bounds: tuple[float, float, float, float]) -> None:
        async with semaphore:
            entries = await _fetch_cell(session, bounds, headers)
            for entry in entries:
                if entry.flight_id:
                    aircraft_by_id[entry.flight_id] = entry
            await asyncio.sleep(_REQUEST_DELAY)

    log.info("Fetching %d cells", len(cells))
    async with AsyncSession(impersonate="chrome") as session:
        await asyncio.gather(*(bounded_fetch(session, b) for b in cells))

    log.info("Fetched %d unique aircraft", len(aircraft_by_id))
    return list(aircraft_by_id.values())
