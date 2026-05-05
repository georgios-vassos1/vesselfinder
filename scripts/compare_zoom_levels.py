"""
Compare the number of vessels returned by MarineTraffic at different zoom levels
over the same geographic centre.

Usage:
    uv run python scripts/compare_zoom_levels.py
"""

import asyncio
from dataclasses import dataclass

from tracker.marine.fetcher import fetch_all, tile_urls
from tracker.marine.scraper import establish_session

_CENTER_X = 22.1
_CENTER_Y = 10.0
_ZOOM_LEVELS = [2, 3, 4, 5]
_OS = "MacOS"


def _marinetraffic_url(zoom: int, cx: float = _CENTER_X, cy: float = _CENTER_Y) -> str:
    return f"https://www.marinetraffic.com/en/ais/home/centerx:{cx}/centery:{cy}/zoom:{zoom}"


@dataclass
class ZoomResult:
    zoom: int
    tiles: int
    vessels: int


async def run() -> None:
    results: list[ZoomResult] = []

    for zoom in _ZOOM_LEVELS:
        print(f"zoom:{zoom}  establishing session ...")
        session = await establish_session(os_name=_OS)
        urls = tile_urls(session.tile_url_template, zoom)
        vessels = await fetch_all(session.tile_url_template, session.cookies, zoom=zoom)

        results.append(ZoomResult(zoom=zoom, tiles=len(urls), vessels=len(vessels)))
        print(f"  → {len(urls)} tiles, {len(vessels)} vessels")

    print("\n--- Summary ---")
    print(f"{'zoom':>6}  {'tiles':>6}  {'vessels':>8}")
    for r in results:
        print(f"{r.zoom:>6}  {r.tiles:>6}  {r.vessels:>8}")


if __name__ == "__main__":
    asyncio.run(run())
