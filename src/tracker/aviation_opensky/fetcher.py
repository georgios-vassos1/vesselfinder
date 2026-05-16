from __future__ import annotations

import json
from dataclasses import dataclass

from curl_cffi.requests import AsyncSession

from tracker.aviation_opensky.proto import RawStateFields, parse_state

_BASE_URL = "https://opensky-network.org/api/states/all"


@dataclass(frozen=True)
class BoundingBox:
    north: float
    south: float
    west: float
    east: float


async def _get(url: str, headers: dict[str, str]) -> bytes:
    async with AsyncSession(impersonate="chrome") as session:
        resp = await session.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.content


async def fetch_states(bbox: BoundingBox, token: str | None = None) -> list[RawStateFields]:
    url = (
        f"{_BASE_URL}"
        f"?lamin={bbox.south}&lamax={bbox.north}"
        f"&lomin={bbox.west}&lomax={bbox.east}"
    )
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = await _get(url, headers)
    data = json.loads(body)
    states = data.get("states") or []
    return [
        parse_state(row)
        for row in states
        if row[6] is not None and row[5] is not None
    ]
