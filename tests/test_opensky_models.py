import dataclasses
from datetime import datetime, timezone

import pytest
from polyfactory.factories.dataclass_factory import DataclassFactory

from tracker.aviation_opensky.models import Aircraft
from tracker.aviation_opensky.proto import RawStateFields

_CAPTURED_AT = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


class RawFactory(DataclassFactory):
    __model__ = RawStateFields


@pytest.fixture
def base_raw():
    return RawFactory.build(
        icao24="abc123",
        lat=51.5,
        lon=-0.1,
        on_ground=False,
    )


def test_from_raw_returns_aircraft(base_raw):
    result = Aircraft.from_raw(base_raw, _CAPTURED_AT, {})
    assert isinstance(result, Aircraft)


def test_from_raw_maps_icao24(base_raw):
    raw = dataclasses.replace(base_raw, icao24="abc123")
    result = Aircraft.from_raw(raw, _CAPTURED_AT, {})
    assert result.icao24 == "abc123"


def test_from_raw_maps_position(base_raw):
    raw = dataclasses.replace(base_raw, lat=51.5, lon=-0.1)
    result = Aircraft.from_raw(raw, _CAPTURED_AT, {})
    assert result.lat == 51.5
    assert result.lon == -0.1


def test_from_raw_sets_captured_at(base_raw):
    result = Aircraft.from_raw(base_raw, _CAPTURED_AT, {})
    assert result.captured_at == _CAPTURED_AT


def test_from_raw_resolves_type_from_opensky_db(base_raw):
    raw = dataclasses.replace(base_raw, icao24="abc123")
    db = {"ABC123": ("B738", "G-TAWX")}
    result = Aircraft.from_raw(raw, _CAPTURED_AT, db)
    assert result.aircraft_type == "B738"
    assert result.registration == "G-TAWX"


def test_from_raw_type_none_when_icao24_not_in_db(base_raw):
    raw = dataclasses.replace(base_raw, icao24="unknown")
    result = Aircraft.from_raw(raw, _CAPTURED_AT, {})
    assert result.aircraft_type is None
    assert result.registration is None


def test_from_raw_db_lookup_is_case_insensitive(base_raw):
    raw = dataclasses.replace(base_raw, icao24="abc123")
    db = {"ABC123": ("A320", "F-GKXA")}
    result = Aircraft.from_raw(raw, _CAPTURED_AT, db)
    assert result.aircraft_type == "A320"


def test_from_raw_strips_callsign(base_raw):
    raw = dataclasses.replace(base_raw, callsign="BAW71K")
    result = Aircraft.from_raw(raw, _CAPTURED_AT, {})
    assert result.callsign == "BAW71K"


def test_from_raw_null_callsign(base_raw):
    raw = dataclasses.replace(base_raw, callsign=None)
    result = Aircraft.from_raw(raw, _CAPTURED_AT, {})
    assert result.callsign is None
