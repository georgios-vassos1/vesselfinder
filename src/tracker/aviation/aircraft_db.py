from __future__ import annotations

import json
from pathlib import Path

_DEFAULT_PATH = Path(__file__).parents[3] / "data" / "aircraft_db.json"

EnrichmentTuple = tuple[str | None, str | None, str | None]


def load(path: Path = _DEFAULT_PATH) -> dict[str, EnrichmentTuple]:
    if not path.exists():
        return {}
    data: dict = json.loads(path.read_text())
    return {
        fid: (entry.get("type"), entry.get("registration"), entry.get("icao24"))
        for fid, entry in data.items()
    }


def save(entries: dict[str, EnrichmentTuple], path: Path = _DEFAULT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing: dict = json.loads(path.read_text()) if path.exists() else {}
    for fid, (type_, reg, icao24) in entries.items():
        existing[fid] = {"type": type_, "registration": reg, "icao24": icao24}
    path.write_text(json.dumps(existing, indent=2, sort_keys=True))
