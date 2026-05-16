import dataclasses
from datetime import datetime, timezone

from tracker.aviation.models import Aircraft
from tracker.aviation.proto import RawAircraftFields

_CAPTURED_AT = datetime(2026, 5, 5, 12, 0, 0, tzinfo=timezone.utc)

_RAW = RawAircraftFields(
    flight_id=0x2B4E1F,
    lat=51.505,
    lon=-0.1,
    heading=270,
    altitude=35000,
    speed=450,
    last_seen=1234567890,
    on_ground=False,
    callsign="BAW123",
)


def test_from_proto_identity():
    a = Aircraft.from_proto(_RAW, _CAPTURED_AT)
    assert a.flight_id == "2b4e1f"
    assert a.callsign == "BAW123"


def test_from_proto_position():
    a = Aircraft.from_proto(_RAW, _CAPTURED_AT)
    assert a.lat == 51.505
    assert a.lon == -0.1
    assert a.altitude == 35000


def test_from_proto_movement():
    a = Aircraft.from_proto(_RAW, _CAPTURED_AT)
    assert a.speed == 450
    assert a.heading == 270
    assert a.vspeed is None


def test_from_proto_on_ground_false():
    a = Aircraft.from_proto(_RAW, _CAPTURED_AT)
    assert a.on_ground is False


def test_from_proto_on_ground_true():
    a = Aircraft.from_proto(dataclasses.replace(_RAW, on_ground=True), _CAPTURED_AT)
    assert a.on_ground is True


def test_from_proto_on_ground_absent():
    a = Aircraft.from_proto(dataclasses.replace(_RAW, on_ground=None), _CAPTURED_AT)
    assert a.on_ground is None


def test_from_proto_captured_at():
    a = Aircraft.from_proto(_RAW, _CAPTURED_AT)
    assert a.captured_at == _CAPTURED_AT


def test_from_proto_empty_callsign_becomes_none():
    a = Aircraft.from_proto(dataclasses.replace(_RAW, callsign="   "), _CAPTURED_AT)
    assert a.callsign is None


def test_from_proto_lookup_fields_absent():
    a = Aircraft.from_proto(_RAW, _CAPTURED_AT)
    assert a.icao24 is None
    assert a.registration is None
    assert a.aircraft_type is None
    assert a.origin is None
    assert a.destination is None
    assert a.flight_number is None
    assert a.squawk is None


def test_from_proto_zero_flight_id():
    a = Aircraft.from_proto(dataclasses.replace(_RAW, flight_id=0), _CAPTURED_AT)
    assert a.flight_id == ""


def test_from_proto_last_seen():
    a = Aircraft.from_proto(_RAW, _CAPTURED_AT)
    assert a.last_seen == 1234567890
