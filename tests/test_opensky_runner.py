import dataclasses
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from polyfactory.factories.dataclass_factory import DataclassFactory

from tracker.aviation_opensky.proto import RawStateFields
from tracker.aviation_opensky.runner import _scrape_once


class RawFactory(DataclassFactory):
    __model__ = RawStateFields


def _mock_conn():
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.__enter__ = MagicMock(return_value=mock_cur)
    mock_cur.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value = mock_cur
    return mock_conn


async def test_scrape_once_returns_insert_count():
    raw = RawFactory.build(icao24="abc123", lat=51.5, lon=-0.1)
    with (
        patch("tracker.aviation_opensky.runner.fetch_states", new_callable=AsyncMock, return_value=[raw]),
        patch("tracker.aviation_opensky.runner.insert_aircraft", return_value=1),
    ):
        result = await _scrape_once(_mock_conn(), {})
    assert result == 1


async def test_scrape_once_resolves_type_from_opensky_db():
    raw = RawFactory.build(icao24="abc123", lat=51.5, lon=-0.1)
    opensky_db = {"ABC123": ("B738", "G-TAWX")}

    inserted = []

    def capture(conn, aircraft):
        inserted.extend(aircraft)
        return len(aircraft)

    with (
        patch("tracker.aviation_opensky.runner.fetch_states", new_callable=AsyncMock, return_value=[raw]),
        patch("tracker.aviation_opensky.runner.insert_aircraft", side_effect=capture),
    ):
        await _scrape_once(_mock_conn(), opensky_db)

    assert inserted[0].aircraft_type == "B738"
    assert inserted[0].registration == "G-TAWX"


async def test_scrape_once_no_type_when_icao24_not_in_db():
    raw = RawFactory.build(icao24="unknown1", lat=51.5, lon=-0.1)

    inserted = []

    def capture(conn, aircraft):
        inserted.extend(aircraft)
        return len(aircraft)

    with (
        patch("tracker.aviation_opensky.runner.fetch_states", new_callable=AsyncMock, return_value=[raw]),
        patch("tracker.aviation_opensky.runner.insert_aircraft", side_effect=capture),
    ):
        await _scrape_once(_mock_conn(), {})

    assert inserted[0].aircraft_type is None
    assert inserted[0].registration is None


async def test_scrape_once_passes_bbox_to_fetcher():
    from tracker.aviation_opensky.fetcher import BoundingBox

    bbox = BoundingBox(north=60.0, south=45.0, west=-10.0, east=20.0)

    with (
        patch("tracker.aviation_opensky.runner.fetch_states", new_callable=AsyncMock, return_value=[]) as mock_fetch,
        patch("tracker.aviation_opensky.runner.insert_aircraft", return_value=0),
    ):
        await _scrape_once(_mock_conn(), {}, bbox=bbox)

    mock_fetch.assert_called_once_with(bbox, token=None)


async def test_scrape_once_passes_token_to_fetcher():
    from tracker.aviation_opensky.fetcher import BoundingBox

    bbox = BoundingBox(north=60.0, south=45.0, west=-10.0, east=20.0)

    with (
        patch("tracker.aviation_opensky.runner.fetch_states", new_callable=AsyncMock, return_value=[]) as mock_fetch,
        patch("tracker.aviation_opensky.runner.insert_aircraft", return_value=0),
    ):
        await _scrape_once(_mock_conn(), {}, bbox=bbox, token="tok123")

    mock_fetch.assert_called_once_with(bbox, token="tok123")
