"""
Fetch all vessels across the full world tile grid and validate consistency.

Runs two consecutive fetches and compares SHIP_ID sets to confirm that coverage
is stable across runs. A Jaccard similarity >= 0.90 is considered acceptable.

Usage:
    uv run python scripts/fetch_all_vessels.py
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from tracker.marine.fetcher import _DEFAULT_ZOOM, fetch_all
from tracker.marine.scraper import establish_session

_OS = "MacOS"
_ZOOM = _DEFAULT_ZOOM
_OUT_DIR = Path(__file__).parent.parent / "data"
_JACCARD_THRESHOLD = 0.90


def _ship_ids(vessels: list[dict]) -> set[str]:
    return {v["SHIP_ID"] for v in vessels if v.get("SHIP_ID")}


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def _region(lat: float, lon: float) -> str:
    if lon > 95 and lat < 25:
        return "SE Asia"
    if lon > 100 and lat > 25:
        return "NE Asia"
    if 0 < lon < 40 and lat > 45:
        return "Northern Europe"
    if -10 < lon < 40 and 30 < lat < 47:
        return "Mediterranean"
    if -100 < lon < -60 and lat > 20:
        return "North America"
    if lon < -60 and lat < 20:
        return "Caribbean/S.America"
    if 45 < lon < 65 and 20 < lat < 30:
        return "Persian Gulf"
    return "Other"


def _coverage_report(vessels: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for v in vessels:
        try:
            region = _region(float(v["LAT"]), float(v["LON"]))
        except (KeyError, ValueError, TypeError):
            region = "Unknown"
        counts[region] = counts.get(region, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: -x[1]))


async def run() -> None:
    print(f"Establishing session ({_OS}) ...")
    session = await establish_session(os_name=_OS)
    print(f"Session ready — tile template: {session.tile_url_template}")
    print(f"Cookies: {len(session.cookies)}")

    results = []
    for run_idx in range(1, 3):
        print(f"\n--- Run {run_idx}/2  (zoom:{_ZOOM}) ---")
        vessels = await fetch_all(session.tile_url_template, session.cookies, zoom=_ZOOM)
        print(f"Fetched {len(vessels)} unique vessels")
        results.append(vessels)

    run1, run2 = results
    ids1, ids2 = _ship_ids(run1), _ship_ids(run2)
    jaccard = _jaccard(ids1, ids2)
    only_run1 = len(ids1 - ids2)
    only_run2 = len(ids2 - ids1)
    common = len(ids1 & ids2)

    print("\n=== Consistency Report ===")
    print(f"Run 1 vessels : {len(run1):>7,}")
    print(f"Run 2 vessels : {len(run2):>7,}")
    print(f"Common        : {common:>7,}")
    print(f"Only run 1    : {only_run1:>7,}")
    print(f"Only run 2    : {only_run2:>7,}")
    print(f"Jaccard sim.  : {jaccard:.3f}  ({'OK' if jaccard >= _JACCARD_THRESHOLD else 'BELOW THRESHOLD'})")

    print("\n=== Geographic Coverage (run 1) ===")
    for region, count in _coverage_report(run1).items():
        print(f"  {region:<25} {count:>6,}")

    _OUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y.%m.%d-%H.%M")
    out_path = _OUT_DIR / f"vessels_{timestamp}.json"
    out_path.write_text(json.dumps(run1, indent=2))
    print(f"\nSaved {len(run1)} vessels → {out_path}")


if __name__ == "__main__":
    asyncio.run(run())
