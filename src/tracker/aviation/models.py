from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from tracker._coerce import to_str
from tracker.aviation.proto import RawAircraftFields


@dataclass
class Aircraft:
    # Identity — from live feed
    flight_id: str
    callsign: str | None     # ICAO ATC callsign e.g. "BAW71K"

    # Identity — not in live feed (available via separate lookup)
    icao24: str | None            # Mode-S hex address
    registration: str | None
    aircraft_type: str | None     # ICAO type code e.g. "B738"
    origin: str | None            # IATA airport
    destination: str | None       # IATA airport
    flight_number: str | None     # IATA flight number e.g. "BA123" (not in live feed)

    # Position
    lat: float | None
    lon: float | None
    altitude: int | None          # feet
    on_ground: bool | None

    # Movement
    speed: int | None             # knots (ground speed)
    heading: int | None           # degrees (0–360)
    vspeed: int | None            # ft/min (not in live feed)

    # ATC
    squawk: str | None            # not in live feed

    # Timing
    last_seen: int | None         # unix timestamp from ADS-B message
    captured_at: datetime

    @classmethod
    def from_proto(cls, raw: RawAircraftFields, captured_at: datetime) -> Aircraft:
        return cls(
            flight_id=format(raw.flight_id, "x") if raw.flight_id else "",
            callsign=to_str(raw.callsign),
            icao24=None,
            registration=None,
            aircraft_type=None,
            origin=None,
            destination=None,
            flight_number=None,
            lat=raw.lat,
            lon=raw.lon,
            altitude=raw.altitude,
            on_ground=raw.on_ground,
            speed=raw.speed,
            heading=raw.heading,
            vspeed=None,
            squawk=None,
            last_seen=raw.last_seen,
            captured_at=captured_at,
        )
