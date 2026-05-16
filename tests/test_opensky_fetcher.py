import json
from unittest.mock import AsyncMock, patch

import pytest

from tracker.aviation_opensky.fetcher import BoundingBox, fetch_states
from tracker.aviation_opensky.proto import RawStateFields


def _api_response(states: list[list]) -> bytes:
    return json.dumps({"time": 1700000000, "states": states}).encode()


def _state_row(icao24="abc123"):
    return [
        icao24, "BAW71K ", "United Kingdom", 1700000000, 1700000001,
        -0.1, 51.5, 11000.0, False, 250.0, 90.0, 0.0,
        None, 11100.0, "1234", False, 0,
    ]


@pytest.fixture
def bbox():
    return BoundingBox(north=60.0, south=45.0, west=-10.0, east=20.0)


async def test_fetch_states_returns_list_of_raw_state_fields(bbox):
    with patch("tracker.aviation_opensky.fetcher._get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = _api_response([_state_row()])
        result = await fetch_states(bbox)
    assert len(result) == 1
    assert isinstance(result[0], RawStateFields)


async def test_fetch_states_returns_empty_list_when_no_states(bbox):
    with patch("tracker.aviation_opensky.fetcher._get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = json.dumps({"time": 1700000000, "states": None}).encode()
        result = await fetch_states(bbox)
    assert result == []


async def test_fetch_states_passes_bbox_to_api(bbox):
    with patch("tracker.aviation_opensky.fetcher._get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = _api_response([])
        await fetch_states(bbox)
    url = mock_get.call_args[0][0]
    assert "lamin=45.0" in url
    assert "lamax=60.0" in url
    assert "lomin=-10.0" in url
    assert "lomax=20.0" in url


async def test_fetch_states_maps_icao24(bbox):
    with patch("tracker.aviation_opensky.fetcher._get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = _api_response([_state_row(icao24="abc123")])
        result = await fetch_states(bbox)
    assert result[0].icao24 == "abc123"


async def test_fetch_states_skips_rows_without_position(bbox):
    row = _state_row()
    row[6] = None  # latitude
    with patch("tracker.aviation_opensky.fetcher._get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = _api_response([row])
        result = await fetch_states(bbox)
    assert result == []


async def test_fetch_states_sends_bearer_token_when_provided(bbox):
    with patch("tracker.aviation_opensky.fetcher._get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = _api_response([])
        await fetch_states(bbox, token="tok123")
    headers = mock_get.call_args[0][1]
    assert headers["Authorization"] == "Bearer tok123"


async def test_fetch_states_sends_no_auth_header_when_token_absent(bbox):
    with patch("tracker.aviation_opensky.fetcher._get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = _api_response([])
        await fetch_states(bbox)
    headers = mock_get.call_args[0][1]
    assert "Authorization" not in headers
