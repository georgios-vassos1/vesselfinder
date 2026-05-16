import dataclasses
from unittest.mock import MagicMock, call

from polyfactory.factories.dataclass_factory import DataclassFactory

from tracker.aviation_opensky.models import Aircraft
from tracker.aviation_opensky.storage import insert_aircraft


class AircraftFactory(DataclassFactory):
    __model__ = Aircraft


def _mock_conn():
    mock_copy = MagicMock()
    mock_copy.__enter__ = MagicMock(return_value=mock_copy)
    mock_copy.__exit__ = MagicMock(return_value=False)
    mock_cur = MagicMock()
    mock_cur.__enter__ = MagicMock(return_value=mock_cur)
    mock_cur.__exit__ = MagicMock(return_value=False)
    mock_cur.copy.return_value = mock_copy
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    return mock_conn, mock_cur, mock_copy


def test_insert_aircraft_empty_returns_zero():
    mock_conn, _, _ = _mock_conn()
    assert insert_aircraft(mock_conn, []) == 0
    mock_conn.cursor.assert_not_called()


def test_insert_aircraft_returns_count():
    mock_conn, _, _ = _mock_conn()
    aircraft = AircraftFactory.batch(3)
    assert insert_aircraft(mock_conn, aircraft) == 3


def test_insert_aircraft_commits():
    mock_conn, _, _ = _mock_conn()
    insert_aircraft(mock_conn, AircraftFactory.batch(1))
    mock_conn.commit.assert_called_once()


def test_insert_aircraft_writes_one_row_per_aircraft():
    mock_conn, _, mock_copy = _mock_conn()
    aircraft = AircraftFactory.batch(2)
    insert_aircraft(mock_conn, aircraft)
    assert mock_copy.write_row.call_count == 2


def test_insert_aircraft_row_starts_with_captured_at_and_icao24():
    mock_conn, _, mock_copy = _mock_conn()
    a = AircraftFactory.build(icao24="abc123")
    insert_aircraft(mock_conn, [a])
    row = mock_copy.write_row.call_args[0][0]
    assert row[0] == a.captured_at
    assert row[1] == "abc123"
