"""
Unit tests for the storage layer that do not require a live database.
"""

import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from vessel_tracker.models import Vessel
from vessel_tracker.storage import _database_url, insert_vessels


def _make_vessel(**kwargs) -> Vessel:
    defaults = dict(
        ship_id="123",
        shipname="TEST",
        flag="GR",
        shiptype=7,
        gt_shiptype=11,
        type_name="Cargo",
        status_name="Under way",
        lat=37.9,
        lon=23.7,
        speed=12.5,
        course=180.0,
        heading=181.0,
        rot=0.0,
        length=200.0,
        width=30.0,
        l_fore=80.0,
        w_left=15.0,
        dwt=50000,
        destination="PIRAEUS",
        elapsed=60,
        captured_at=datetime(2026, 5, 3, 12, 0, 0, tzinfo=timezone.utc),
    )
    return Vessel(**{**defaults, **kwargs})


def test_database_url_raises_without_env():
    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("DATABASE_URL", None)
        with pytest.raises(RuntimeError, match="DATABASE_URL"):
            _database_url()


def test_database_url_returns_env_value():
    with patch.dict(os.environ, {"DATABASE_URL": "postgresql://localhost/test"}):
        assert _database_url() == "postgresql://localhost/test"


def test_insert_vessels_uses_copy_protocol():
    vessels = [_make_vessel(ship_id="1"), _make_vessel(ship_id="2")]

    mock_copy = MagicMock()
    mock_copy.__enter__ = MagicMock(return_value=mock_copy)
    mock_copy.__exit__ = MagicMock(return_value=False)

    mock_cur = MagicMock()
    mock_cur.copy.return_value = mock_copy
    mock_cur.__enter__ = MagicMock(return_value=mock_cur)
    mock_cur.__exit__ = MagicMock(return_value=False)

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur

    result = insert_vessels(mock_conn, vessels)

    assert result == 2
    mock_cur.copy.assert_called_once()
    assert mock_copy.write_row.call_count == 2
    mock_conn.commit.assert_called_once()


def test_insert_vessels_empty_returns_zero():
    mock_conn = MagicMock()
    result = insert_vessels(mock_conn, [])
    assert result == 0
    mock_conn.cursor.assert_not_called()
    mock_conn.commit.assert_not_called()


def test_insert_vessels_row_order():
    """Verify captured_at is the first element in each COPY row (hypertable partition key)."""
    captured_at = datetime(2026, 5, 3, 12, 0, 0, tzinfo=timezone.utc)
    vessel = _make_vessel(ship_id="42", captured_at=captured_at)

    mock_copy = MagicMock()
    mock_copy.__enter__ = MagicMock(return_value=mock_copy)
    mock_copy.__exit__ = MagicMock(return_value=False)

    mock_cur = MagicMock()
    mock_cur.copy.return_value = mock_copy
    mock_cur.__enter__ = MagicMock(return_value=mock_cur)
    mock_cur.__exit__ = MagicMock(return_value=False)

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur

    insert_vessels(mock_conn, [vessel])

    row = mock_copy.write_row.call_args[0][0]
    assert row[0] == captured_at   # captured_at first — partition key
    assert row[1] == "42"          # ship_id second
