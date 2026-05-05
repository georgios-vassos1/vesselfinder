from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from polyfactory.factories.dataclass_factory import DataclassFactory

from tracker.marine.models import Vessel
from tracker.marine.storage import insert_vessels
from tracker.storage import _database_url


class VesselFactory(DataclassFactory[Vessel]):
    __model__ = Vessel
    captured_at = datetime(2026, 5, 3, 12, 0, 0, tzinfo=timezone.utc)


def _mock_conn():
    mock_copy = MagicMock()
    mock_copy.__enter__ = MagicMock(return_value=mock_copy)
    mock_copy.__exit__ = MagicMock(return_value=False)

    mock_cur = MagicMock()
    mock_cur.copy.return_value = mock_copy
    mock_cur.__enter__ = MagicMock(return_value=mock_cur)
    mock_cur.__exit__ = MagicMock(return_value=False)

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    return mock_conn, mock_cur, mock_copy


def test_database_url_raises_without_env():
    with pytest.MonkeyPatch.context() as mp:
        mp.delenv("DATABASE_URL", raising=False)
        with pytest.raises(RuntimeError, match="DATABASE_URL"):
            _database_url()


def test_database_url_returns_env_value():
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("DATABASE_URL", "postgresql://localhost/test")
        assert _database_url() == "postgresql://localhost/test"


def test_insert_vessels_uses_copy_protocol():
    vessels = VesselFactory.batch(2)
    mock_conn, mock_cur, mock_copy = _mock_conn()

    result = insert_vessels(mock_conn, vessels)

    assert result == 2
    mock_cur.copy.assert_called_once()
    assert mock_copy.write_row.call_count == 2
    mock_conn.commit.assert_called_once()


def test_insert_vessels_empty_returns_zero():
    mock_conn, _, _ = _mock_conn()
    result = insert_vessels(mock_conn, [])
    assert result == 0
    mock_conn.cursor.assert_not_called()
    mock_conn.commit.assert_not_called()


def test_insert_vessels_row_order():
    """captured_at must be the first element in each COPY row (hypertable partition key)."""
    captured_at = datetime(2026, 5, 3, 12, 0, 0, tzinfo=timezone.utc)
    vessel = VesselFactory.build(ship_id="42", captured_at=captured_at)
    mock_conn, _, mock_copy = _mock_conn()

    insert_vessels(mock_conn, [vessel])

    row = mock_copy.write_row.call_args[0][0]
    assert row[0] == captured_at
    assert row[1] == "42"
