from __future__ import annotations

from dataclasses import dataclass

_METERS_TO_FEET = 3.28084
_MPS_TO_KNOTS = 1.94384


@dataclass
class RawStateFields:
    icao24: str
    callsign: str | None
    lat: float | None
    lon: float | None
    altitude: int | None       # feet (converted from meters)
    on_ground: bool
    speed: int | None          # knots (converted from m/s)
    heading: float | None      # degrees
    squawk: str | None
    last_contact: int          # unix timestamp


def parse_state(row: list) -> RawStateFields:
    baro_alt = row[7]
    velocity = row[9]
    callsign = row[1]
    return RawStateFields(
        icao24=row[0],
        callsign=callsign.strip() if callsign is not None else None,
        lat=row[6],
        lon=row[5],
        altitude=round(baro_alt * _METERS_TO_FEET) if baro_alt is not None else None,
        on_ground=row[8],
        speed=round(velocity * _MPS_TO_KNOTS) if velocity is not None else None,
        heading=row[10],
        squawk=row[14],
        last_contact=row[4],
    )
