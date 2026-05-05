from datetime import datetime, timezone

from tracker.marine.models import AISRecord, Vessel

_CAPTURED_AT = datetime(2026, 5, 3, 12, 0, 0, tzinfo=timezone.utc)

_RAW: AISRecord = {
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
}


def test_from_raw_identity():
    v = Vessel.from_raw(_RAW, _CAPTURED_AT)
    assert v.ship_id == "7378535"
    assert v.shipname == "MONTEVIDEO EXPRESS"
    assert v.flag == "DE"
    assert v.shiptype == 7


def test_from_raw_position():
    v = Vessel.from_raw(_RAW, _CAPTURED_AT)
    assert v.lat == -12.927524
    assert v.lon == -172.375


def test_from_raw_speed_converted_to_knots():
    v = Vessel.from_raw(_RAW, _CAPTURED_AT)
    assert v.speed == 17.5


def test_from_raw_dimensions():
    v = Vessel.from_raw(_RAW, _CAPTURED_AT)
    assert v.length == 335.0
    assert v.width == 51.0
    assert v.dwt == 142411


def test_from_raw_captured_at():
    v = Vessel.from_raw(_RAW, _CAPTURED_AT)
    assert v.captured_at == _CAPTURED_AT


def test_from_raw_null_fields():
    raw: AISRecord = {**_RAW, "SPEED": None, "HEADING": None, "FLAG": None}
    v = Vessel.from_raw(raw, _CAPTURED_AT)
    assert v.speed is None
    assert v.heading is None
    assert v.flag is None


def test_from_raw_empty_strings_become_none():
    raw: AISRecord = {**_RAW, "FLAG": "", "TYPE_NAME": "  ", "DESTINATION": ""}
    v = Vessel.from_raw(raw, _CAPTURED_AT)
    assert v.flag is None
    assert v.type_name is None
    assert v.destination is None
