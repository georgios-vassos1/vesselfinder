"""
Compare vessel counts across different geographic centres at a fixed zoom level.

Tests major shipping regions to understand how centre coordinates affect coverage.

Usage:
    uv run python scripts/compare_centers.py
"""

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path

import aiohttp

from vessel_tracker.ais_data_scraper import _filter_ais_urls
from vessel_tracker.config import BROWSER_EXECUTABLES, REQUEST_HEADERS
from vessel_tracker.session import _get_xhr_requests

_ZOOM = 2
_OS = "MacOS"
_COOKIES_FILE = Path(__file__).parent.parent / "cookies.json"

_CENTRES = {
    "Gulf of Guinea (default)": (22.1, 10.0),
    "English Channel":          (1.5,  51.0),
    "Mediterranean":            (15.0, 35.0),
    "Strait of Malacca":        (103.8, 1.3),
    "South China Sea":          (114.0, 15.0),
    "US East Coast":            (-74.0, 40.7),
    "Persian Gulf":             (53.0,  25.0),
    "North Sea":                (4.5,  56.0),
}


def _load_cookies() -> list[dict] | None:
    if _COOKIES_FILE.exists():
        cookies = json.loads(_COOKIES_FILE.read_text())
        print(f"Loaded {len(cookies)} cookies from {_COOKIES_FILE.name}")
        return cookies
    print(f"No {_COOKIES_FILE.name} found — proceeding without cookies (may be blocked)")
    return None


def _marinetraffic_url(cx: float, cy: float, zoom: int = _ZOOM) -> str:
    return f"https://www.marinetraffic.com/en/ais/home/centerx:{cx}/centery:{cy}/zoom:{zoom}"


async def _fetch_tile_responses(urls: list[str], headers: dict) -> list[dict]:
    async def _get(session: aiohttp.ClientSession, url: str) -> dict | None:
        try:
            async with session.get(url, headers=headers) as resp:
                resp.raise_for_status()
                return await resp.json()
        except Exception as exc:
            print(f"  skipped {url}: {exc}")
            return None

    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(*(_get(session, url) for url in urls))
    return [r for r in results if r is not None]


def _count_vessels(responses: list) -> int:
    total = 0
    for r in responses:
        if isinstance(r, dict) and "data" in r and isinstance(r["data"], dict):
            total += len(r["data"].get("rows") or [])
    return total


@dataclass
class CentreResult:
    name: str
    cx: float
    cy: float
    tiles: int
    vessels: int


async def run() -> None:
    browser_args = BROWSER_EXECUTABLES[_OS]
    cookies = _load_cookies()
    results: list[CentreResult] = []

    for name, (cx, cy) in _CENTRES.items():
        url = _marinetraffic_url(cx, cy)
        print(f"{name:30s}  fetching ...")

        xhr_requests = await _get_xhr_requests(*browser_args, url=url, headless=False, cookies=cookies)
        ais_urls = _filter_ais_urls(xhr_requests)
        responses = await _fetch_tile_responses(ais_urls, REQUEST_HEADERS)
        vessels = _count_vessels(responses)

        results.append(CentreResult(name=name, cx=cx, cy=cy, tiles=len(ais_urls), vessels=vessels))
        print(f"  → {len(ais_urls)} tiles, {vessels} vessels")

    results.sort(key=lambda r: r.vessels, reverse=True)

    print(f"\n--- Summary (zoom:{_ZOOM}) ---")
    print(f"{'centre':<30}  {'tiles':>6}  {'vessels':>8}")
    for r in results:
        print(f"{r.name:<30}  {r.tiles:>6}  {r.vessels:>8}")


if __name__ == "__main__":
    asyncio.run(run())
