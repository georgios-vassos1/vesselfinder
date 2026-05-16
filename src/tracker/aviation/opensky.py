from __future__ import annotations

import csv
import io
import json
import logging
import urllib.request
from pathlib import Path

log = logging.getLogger(__name__)

_DB_PATH = Path(__file__).parents[3] / "data" / "opensky_db.json"
_CSV_URL = "https://opensky-network.org/datasets/metadata/aircraftDatabase.csv"


def load(path: Path = _DB_PATH) -> dict[str, tuple[str | None, str | None]]:
    if not path.exists():
        return {}
    data: dict = json.loads(path.read_text())
    return {icao24: (entry.get("type"), entry.get("registration")) for icao24, entry in data.items()}


def download(path: Path = _DB_PATH) -> int:
    log.info("Downloading OpenSky aircraft database…")
    with urllib.request.urlopen(_CSV_URL) as resp:
        content = resp.read().decode("utf-8", errors="replace")

    db: dict = {}
    reader = csv.DictReader(io.StringIO(content))
    for row in reader:
        icao24 = (row.get("icao24") or "").strip().upper()
        if not icao24:
            continue
        db[icao24] = {
            "type": row.get("typecode") or None,
            "registration": row.get("registration") or None,
        }

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(db, indent=2, sort_keys=True))
    log.info("Saved %d aircraft to %s", len(db), path)
    return len(db)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    download()
