import dataclasses

import pytest
from polyfactory.factories.dataclass_factory import DataclassFactory

from tracker.aviation.correlator import correlate
from tracker.aviation.models import Aircraft
from tracker.aviation_opensky.proto import RawStateFields


class AircraftFactory(DataclassFactory):
    __model__ = Aircraft


class StateFactory(DataclassFactory):
    __model__ = RawStateFields


def _fr24(flight_id: str, callsign: str | None, lat: float, lon: float) -> Aircraft:
    return AircraftFactory.build(
        flight_id=flight_id, callsign=callsign, lat=lat, lon=lon, icao24=None,
    )


def _opensky(icao24: str, callsign: str | None, lat: float, lon: float) -> RawStateFields:
    return StateFactory.build(icao24=icao24, callsign=callsign, lat=lat, lon=lon)


def test_correlate_matches_by_callsign_and_close_position():
    fr24 = [_fr24("aabbcc", "BAW71K", 51.5, -0.1)]
    opensky = [_opensky("400EA1", "BAW71K", 51.5, -0.1)]
    assert correlate(fr24, opensky) == {"aabbcc": "400EA1"}


def test_correlate_excludes_match_when_position_too_far():
    fr24 = [_fr24("aabbcc", "BAW71K", 51.5, -0.1)]
    opensky = [_opensky("400EA1", "BAW71K", 60.0, 20.0)]  # > 50km away
    assert correlate(fr24, opensky) == {}


def test_correlate_skips_fr24_aircraft_without_callsign():
    fr24 = [_fr24("aabbcc", None, 51.5, -0.1)]
    opensky = [_opensky("400EA1", "BAW71K", 51.5, -0.1)]
    assert correlate(fr24, opensky) == {}


def test_correlate_skips_opensky_state_without_callsign():
    fr24 = [_fr24("aabbcc", "BAW71K", 51.5, -0.1)]
    opensky = [_opensky("400EA1", None, 51.5, -0.1)]
    assert correlate(fr24, opensky) == {}


def test_correlate_returns_empty_when_no_callsign_match():
    fr24 = [_fr24("aabbcc", "BAW71K", 51.5, -0.1)]
    opensky = [_opensky("400EA1", "EZY123", 51.5, -0.1)]
    assert correlate(fr24, opensky) == {}


def test_correlate_excludes_ambiguous_duplicate_callsigns():
    fr24 = [_fr24("aabbcc", "BAW71K", 51.5, -0.1)]
    opensky = [
        _opensky("400EA1", "BAW71K", 51.5, -0.1),
        _opensky("400EA2", "BAW71K", 51.6, -0.1),
    ]
    assert correlate(fr24, opensky) == {}


def test_correlate_handles_multiple_unambiguous_matches():
    fr24 = [
        _fr24("aabbcc", "BAW71K", 51.5, -0.1),
        _fr24("ddeeff", "EZY123", 48.9, 2.3),
    ]
    opensky = [
        _opensky("400EA1", "BAW71K", 51.5, -0.1),
        _opensky("3C6445", "EZY123", 48.9, 2.3),
    ]
    result = correlate(fr24, opensky)
    assert result == {"aabbcc": "400EA1", "ddeeff": "3C6445"}


def test_correlate_skips_already_enriched_fr24_aircraft():
    fr24 = [AircraftFactory.build(flight_id="aabbcc", callsign="BAW71K", lat=51.5, lon=-0.1, icao24="EXISTING")]
    opensky = [_opensky("400EA1", "BAW71K", 51.5, -0.1)]
    assert correlate(fr24, opensky) == {}


def test_correlate_respects_custom_max_distance():
    fr24 = [_fr24("aabbcc", "BAW71K", 51.5, -0.1)]
    opensky = [_opensky("400EA1", "BAW71K", 51.6, -0.1)]  # ~11km away
    assert correlate(fr24, opensky, max_distance_km=5.0) == {}
    assert correlate(fr24, opensky, max_distance_km=20.0) == {"aabbcc": "400EA1"}
