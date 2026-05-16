from __future__ import annotations

import math
from collections import Counter

from tracker.aviation.models import Aircraft
from tracker.aviation_opensky.proto import RawStateFields


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def correlate(
    fr24: list[Aircraft],
    opensky: list[RawStateFields],
    max_distance_km: float = 50.0,
) -> dict[str, str]:
    opensky_by_callsign: dict[str, list[RawStateFields]] = {}
    for state in opensky:
        if state.callsign:
            opensky_by_callsign.setdefault(state.callsign, []).append(state)

    ambiguous = {cs for cs, states in opensky_by_callsign.items() if len(states) > 1}

    result: dict[str, str] = {}
    for aircraft in fr24:
        if not aircraft.callsign or aircraft.icao24:
            continue
        if aircraft.callsign in ambiguous:
            continue
        candidates = opensky_by_callsign.get(aircraft.callsign, [])
        if not candidates:
            continue
        state = candidates[0]
        if state.lat is None or state.lon is None or aircraft.lat is None or aircraft.lon is None:
            continue
        dist = _haversine_km(aircraft.lat, aircraft.lon, state.lat, state.lon)
        if dist <= max_distance_km:
            result[aircraft.flight_id] = state.icao24

    return result
