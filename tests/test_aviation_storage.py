from unittest.mock import MagicMock

from tracker.aviation.storage import load_enrichment, store_enrichment


def _mock_conn(fetchall_return=None):
    mock_cur = MagicMock()
    mock_cur.__enter__ = MagicMock(return_value=mock_cur)
    mock_cur.__exit__ = MagicMock(return_value=False)
    mock_cur.fetchall.return_value = fetchall_return or []

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    return mock_conn, mock_cur


def test_load_enrichment_empty_ids_returns_empty_dict():
    mock_conn, mock_cur = _mock_conn()
    result = load_enrichment(mock_conn, [])
    assert result == {}
    mock_cur.execute.assert_not_called()


def test_load_enrichment_returns_dict_keyed_by_flight_id():
    row = {"flight_id": "2b4e1f", "aircraft_type": "B738", "registration": "G-TAWX", "icao24": "400EA1"}
    mock_conn, _ = _mock_conn(fetchall_return=[row])
    result = load_enrichment(mock_conn, ["2b4e1f"])
    assert result == {"2b4e1f": ("B738", "G-TAWX", "400EA1")}


def test_load_enrichment_missing_flight_id_absent_from_result():
    mock_conn, _ = _mock_conn(fetchall_return=[])
    result = load_enrichment(mock_conn, ["unknown"])
    assert "unknown" not in result


def test_store_enrichment_empty_dict_does_nothing():
    mock_conn, mock_cur = _mock_conn()
    store_enrichment(mock_conn, {})
    mock_cur.execute.assert_not_called()
    mock_conn.commit.assert_not_called()


def test_store_enrichment_executes_upsert_per_entry():
    mock_conn, mock_cur = _mock_conn()
    enrichments = {
        "2b4e1f": ("B738", "G-TAWX", "400EA1"),
        "3c4563": ("A320", "F-GKXA", "3C6445"),
    }
    store_enrichment(mock_conn, enrichments)
    assert mock_cur.execute.call_count == 2
    mock_conn.commit.assert_called_once()


def test_store_enrichment_row_contains_flight_id_and_fields():
    mock_conn, mock_cur = _mock_conn()
    store_enrichment(mock_conn, {"2b4e1f": ("B738", "G-TAWX", "400EA1")})
    args = mock_cur.execute.call_args[0][1]
    assert args[0] == "2b4e1f"
    assert args[1] == "B738"
    assert args[2] == "G-TAWX"
    assert args[3] == "400EA1"
