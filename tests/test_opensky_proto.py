import pytest

from tracker.aviation_opensky.proto import RawStateFields, parse_state


def _state(
    icao24="abc123",
    callsign="BAW71K ",
    origin_country="United Kingdom",
    time_position=1700000000,
    last_contact=1700000001,
    longitude=-0.1,
    latitude=51.5,
    baro_altitude=11000.0,
    on_ground=False,
    velocity=250.0,
    true_track=90.0,
    vertical_rate=0.0,
    sensors=None,
    geo_altitude=11100.0,
    squawk="1234",
    spi=False,
    position_source=0,
):
    return [
        icao24, callsign, origin_country, time_position, last_contact,
        longitude, latitude, baro_altitude, on_ground, velocity,
        true_track, vertical_rate, sensors, geo_altitude, squawk,
        spi, position_source,
    ]


def test_parse_state_returns_raw_state_fields():
    result = parse_state(_state())
    assert isinstance(result, RawStateFields)


def test_parse_state_maps_icao24():
    result = parse_state(_state(icao24="abc123"))
    assert result.icao24 == "abc123"


def test_parse_state_strips_callsign_whitespace():
    result = parse_state(_state(callsign="BAW71K "))
    assert result.callsign == "BAW71K"


def test_parse_state_null_callsign_becomes_none():
    result = parse_state(_state(callsign=None))
    assert result.callsign is None


def test_parse_state_maps_position():
    result = parse_state(_state(latitude=51.5, longitude=-0.1))
    assert result.lat == 51.5
    assert result.lon == -0.1


def test_parse_state_converts_baro_altitude_to_feet():
    result = parse_state(_state(baro_altitude=11000.0))
    assert result.altitude == pytest.approx(36089, rel=0.01)


def test_parse_state_null_altitude_becomes_none():
    result = parse_state(_state(baro_altitude=None))
    assert result.altitude is None


def test_parse_state_converts_velocity_to_knots():
    result = parse_state(_state(velocity=257.222))
    assert result.speed == pytest.approx(500, rel=0.01)


def test_parse_state_null_velocity_becomes_none():
    result = parse_state(_state(velocity=None))
    assert result.speed is None


def test_parse_state_maps_heading():
    result = parse_state(_state(true_track=270.0))
    assert result.heading == pytest.approx(270.0)


def test_parse_state_maps_on_ground():
    assert parse_state(_state(on_ground=True)).on_ground is True
    assert parse_state(_state(on_ground=False)).on_ground is False


def test_parse_state_maps_squawk():
    result = parse_state(_state(squawk="7700"))
    assert result.squawk == "7700"


def test_parse_state_null_squawk_becomes_none():
    result = parse_state(_state(squawk=None))
    assert result.squawk is None


def test_parse_state_maps_last_contact():
    result = parse_state(_state(last_contact=1700000001))
    assert result.last_contact == 1700000001
