"""
Compare vessel counts across different geographic centres at a fixed zoom level.

Tests major shipping regions to understand how centre coordinates affect coverage.

Usage:
    uv run python scripts/compare_centers.py
"""

import asyncio
from dataclasses import dataclass

from tracker.marine.fetcher import fetch_all
from tracker.marine.scraper import establish_session

_ZOOM = 2
_OS = "MacOS"

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


@dataclass
class CentreResult:
    name: str
    cx: float
    cy: float
    vessels: int


async def run() -> None:
    results: list[CentreResult] = []

    for name, (cx, cy) in _CENTRES.items():
        print(f"{name:30s}  establishing session ...")
        session = await establish_session(os_name=_OS)
        vessels = await fetch_all(session.tile_url_template, session.cookies, zoom=_ZOOM)

        results.append(CentreResult(name=name, cx=cx, cy=cy, vessels=len(vessels)))
        print(f"  → {len(vessels)} vessels")

    results.sort(key=lambda r: r.vessels, reverse=True)

    print(f"\n--- Summary (zoom:{_ZOOM}) ---")
    print(f"{'centre':<30}  {'vessels':>8}")
    for r in results:
        print(f"{r.name:<30}  {r.vessels:>8}")


if __name__ == "__main__":
    asyncio.run(run())
