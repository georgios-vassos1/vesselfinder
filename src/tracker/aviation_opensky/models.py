from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from tracker.aviation_opensky.proto import RawStateFields


@dataclass
class Aircraft:
    icao24: str
    callsign: str | None
    registration: str | None
    aircraft_type: str | None
    lat: float | None
    lon: float | None
    altitude: int | None       # feet
    on_ground: bool
    speed: int | None          # knots
    heading: float | None      # degrees
    squawk: str | None
    last_contact: int
    captured_at: datetime

    @classmethod
    def from_raw(
        cls,
        raw: RawStateFields,
        captured_at: datetime,
        opensky_db: dict[str, tuple[str | None, str | None]],
    ) -> Aircraft:
        type_, reg = opensky_db.get(raw.icao24.upper(), (None, None))
        return cls(
            icao24=raw.icao24,
            callsign=raw.callsign,
            registration=reg,
            aircraft_type=type_,
            lat=raw.lat,
            lon=raw.lon,
            altitude=raw.altitude,
            on_ground=raw.on_ground,
            speed=raw.speed,
            heading=raw.heading,
            squawk=raw.squawk,
            last_contact=raw.last_contact,
            captured_at=captured_at,
        )
