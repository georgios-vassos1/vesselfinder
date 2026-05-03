"""
Compare the number of vessels returned by MarineTraffic at different zoom levels
over the same geographic centre.

Cookies are loaded from cookies.json if present (ignored by git).
To extract cookies, open MarineTraffic in Chrome, open DevTools → Application →
Cookies, export them as JSON in Playwright format:
  [{"name": "...", "value": "...", "domain": "www.marinetraffic.com", "path": "/"}]

Usage:
    uv run python scripts/compare_zoom_levels.py
"""

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path

import aiohttp

from vessel_tracker.ais_data_scraper import _filter_ais_urls
from vessel_tracker.config import BROWSER_EXECUTABLES, REQUEST_HEADERS
from vessel_tracker.session import _get_xhr_requests

_CENTER_X = 22.1
_CENTER_Y = 10.0
_ZOOM_LEVELS = [2, 3, 4, 5]
_OS = "MacOS"
_COOKIES_FILE = Path(__file__).parent.parent / "cookies.json"


def _load_cookies() -> list[dict] | None:
    if _COOKIES_FILE.exists():
        cookies = json.loads(_COOKIES_FILE.read_text())
        print(f"Loaded {len(cookies)} cookies from {_COOKIES_FILE.name}")
        return cookies
    print(f"No {_COOKIES_FILE.name} found — proceeding without cookies (may be blocked)")
    return None


def _marinetraffic_url(zoom: int, cx: float = _CENTER_X, cy: float = _CENTER_Y) -> str:
    return f"https://www.marinetraffic.com/en/ais/home/centerx:{cx}/centery:{cy}/zoom:{zoom}"


def _count_vessels(responses: list) -> int:
    total = 0
    for r in responses:
        if isinstance(r, dict) and "data" in r and isinstance(r["data"], dict):
            total += len(r["data"].get("rows") or [])
    return total


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


@dataclass
class ZoomResult:
    zoom: int
    tiles: int
    vessels: int


async def run() -> None:
    browser_args = BROWSER_EXECUTABLES[_OS]
    cookies = _load_cookies()
    results: list[ZoomResult] = []

    for zoom in _ZOOM_LEVELS:
        url = _marinetraffic_url(zoom)
        print(f"zoom:{zoom}  fetching {url} ...")

        xhr_requests = await _get_xhr_requests(*browser_args, url=url, headless=False, cookies=cookies)
        ais_urls = _filter_ais_urls(xhr_requests)
        responses = await _fetch_tile_responses(ais_urls, REQUEST_HEADERS)
        vessels = _count_vessels(responses)

        results.append(ZoomResult(zoom=zoom, tiles=len(ais_urls), vessels=vessels))
        print(f"  → {len(ais_urls)} tiles, {vessels} vessels")

    print("\n--- Summary ---")
    print(f"{'zoom':>6}  {'tiles':>6}  {'vessels':>8}")
    for r in results:
        print(f"{r.zoom:>6}  {r.tiles:>6}  {r.vessels:>8}")


if __name__ == "__main__":
    asyncio.run(run())
