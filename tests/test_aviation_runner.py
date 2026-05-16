from unittest.mock import AsyncMock, MagicMock, patch

from tracker.aviation.proto import RawAircraftFields
from tracker.aviation.runner import _scrape_once


def _raw(flight_id: int, callsign: str) -> RawAircraftFields:
    return RawAircraftFields(
        flight_id=flight_id, lat=51.5, lon=-0.1,
        heading=270, altitude=35000, speed=450,
        last_seen=1234567890, on_ground=False, callsign=callsign,
    )


def _mock_conn():
    mock_cur = MagicMock()
    mock_cur.__enter__ = MagicMock(return_value=mock_cur)
    mock_cur.__exit__ = MagicMock(return_value=False)
    mock_cur.fetchall.return_value = []
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    return mock_conn


async def test_scrape_once_skips_enricher_for_aircraft_db_hits():
    flight_id_int = 0x3fb7d4d2
    flight_id_hex = format(flight_id_int, "x")

    aircraft_db = {flight_id_hex: ("B789", "CC-BGK", "E80451")}

    with (
        patch("tracker.aviation.runner.fetch_all", new_callable=AsyncMock) as mock_fetch,
        patch("tracker.aviation.runner.enrich_ids", new_callable=AsyncMock) as mock_enrich,
        patch("tracker.aviation.runner.load_enrichment", return_value={}),
        patch("tracker.aviation.runner.store_enrichment"),
        patch("tracker.aviation.runner.insert_aircraft", return_value=1),
        patch("tracker.aviation.runner.save_aircraft_db"),
    ):
        mock_fetch.return_value = [_raw(flight_id_int, "LAN100")]
        await _scrape_once(_mock_conn(), aircraft_db)

    mock_enrich.assert_not_called()


async def test_scrape_once_applies_aircraft_db_type_to_inserted_aircraft():
    flight_id_int = 0x3fb7d4d2
    flight_id_hex = format(flight_id_int, "x")

    aircraft_db = {flight_id_hex: ("B789", "CC-BGK", "E80451")}

    inserted = []

    def capture_insert(conn, aircraft):
        inserted.extend(aircraft)
        return len(aircraft)

    with (
        patch("tracker.aviation.runner.fetch_all", new_callable=AsyncMock) as mock_fetch,
        patch("tracker.aviation.runner.enrich_ids", new_callable=AsyncMock),
        patch("tracker.aviation.runner.load_enrichment", return_value={}),
        patch("tracker.aviation.runner.store_enrichment"),
        patch("tracker.aviation.runner.insert_aircraft", side_effect=capture_insert),
        patch("tracker.aviation.runner.save_aircraft_db"),
    ):
        mock_fetch.return_value = [_raw(flight_id_int, "LAN100")]
        await _scrape_once(_mock_conn(), aircraft_db)

    assert inserted[0].aircraft_type == "B789"
    assert inserted[0].registration == "CC-BGK"
    assert inserted[0].icao24 == "E80451"


async def test_scrape_once_calls_enricher_for_ids_missing_from_both_sources():
    flight_id_int = 0xdeadbeef
    flight_id_hex = format(flight_id_int, "x")

    aircraft_db: dict = {}

    with (
        patch("tracker.aviation.runner.fetch_all", new_callable=AsyncMock) as mock_fetch,
        patch("tracker.aviation.runner.enrich_ids", new_callable=AsyncMock) as mock_enrich,
        patch("tracker.aviation.runner.load_enrichment", return_value={}),
        patch("tracker.aviation.runner.store_enrichment"),
        patch("tracker.aviation.runner.insert_aircraft", return_value=1),
        patch("tracker.aviation.runner.save_aircraft_db"),
    ):
        mock_fetch.return_value = [_raw(flight_id_int, "DAL123")]
        mock_enrich.return_value = {}
        await _scrape_once(_mock_conn(), aircraft_db)

    mock_enrich.assert_called_once()
    assert flight_id_hex in mock_enrich.call_args[0][0]
