from datetime import datetime, timezone

from vessel_tracker.models import Vessel

_RAW = {
    "SHIP_ID": "7378535",
    "SHIPNAME": "MONTEVIDEO EXPRESS",
    "FLAG": "DE",
    "SHIPTYPE": "7",
    "GT_SHIPTYPE": "11",
    "TYPE_NAME": "Cargo",
    "STATUS_NAME": "Under way",
    "LAT": "-12.927524",
    "LON": "-172.375",
    "SPEED": "175",
    "COURSE": "301",
    "HEADING": "300",
    "ROT": "2",
    "LENGTH": "335",
    "WIDTH": "51",
    "L_FORE": "130",
    "W_LEFT": "33",
    "DWT": "142411",
    "DESTINATION": "CLSVE>>CNYTN",
    "ELAPSED": "1233",
    "captured_at": "2026-05-03T12:00:00+00:00",
}


def test_from_raw_identity():
    v = Vessel.from_raw(_RAW)
    assert v.ship_id == "7378535"
    assert v.shipname == "MONTEVIDEO EXPRESS"
    assert v.flag == "DE"
    assert v.shiptype == 7


def test_from_raw_position():
    v = Vessel.from_raw(_RAW)
    assert v.lat == -12.927524
    assert v.lon == -172.375


def test_from_raw_speed_converted_to_knots():
    v = Vessel.from_raw(_RAW)
    assert v.speed == 17.5  # 175 tenths-of-knot → 17.5 kn


def test_from_raw_dimensions():
    v = Vessel.from_raw(_RAW)
    assert v.length == 335.0
    assert v.width == 51.0
    assert v.dwt == 142411


def test_from_raw_captured_at():
    v = Vessel.from_raw(_RAW)
    assert isinstance(v.captured_at, datetime)
    assert v.captured_at == datetime(2026, 5, 3, 12, 0, 0, tzinfo=timezone.utc)


def test_from_raw_null_fields():
    raw = {**_RAW, "SPEED": None, "HEADING": None, "FLAG": None}
    v = Vessel.from_raw(raw)
    assert v.speed is None
    assert v.heading is None
    assert v.flag is None


def test_from_raw_missing_captured_at_defaults_to_now():
    raw = {k: v for k, v in _RAW.items() if k != "captured_at"}
    v = Vessel.from_raw(raw)
    assert v.captured_at.tzinfo is not None


def test_from_raw_empty_strings_become_none():
    raw = {**_RAW, "FLAG": "", "TYPE_NAME": "  ", "DESTINATION": ""}
    v = Vessel.from_raw(raw)
    assert v.flag is None
    assert v.type_name is None
    assert v.destination is None
