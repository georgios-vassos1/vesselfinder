from unittest.mock import AsyncMock, MagicMock, patch

from tracker.aviation.enricher import _parse_clickhandler, enrich_ids


def test_parse_clickhandler_populates_all_fields():
    data = {"aircraft": {"model": {"code": "B738"}, "registration": "G-TAWX", "hex": "400ea1"}}
    at, reg, icao = _parse_clickhandler(data)
    assert at == "B738"
    assert reg == "G-TAWX"
    assert icao == "400EA1"


def test_parse_clickhandler_hex_uppercased():
    data = {"aircraft": {"model": {"code": "A320"}, "registration": "F-GKXA", "hex": "3c6445"}}
    _, _, icao = _parse_clickhandler(data)
    assert icao == "3C6445"


def test_parse_clickhandler_missing_aircraft_key_returns_nones():
    at, reg, icao = _parse_clickhandler({})
    assert at is None
    assert reg is None
    assert icao is None


def test_parse_clickhandler_empty_hex_returns_none():
    data = {"aircraft": {"model": {"code": "B77W"}, "registration": "N123", "hex": ""}}
    _, _, icao = _parse_clickhandler(data)
    assert icao is None


async def test_enrich_ids_empty_list_returns_empty_dict():
    result = await enrich_ids([])
    assert result == {}


async def test_enrich_ids_returns_dict_keyed_by_flight_id():
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "aircraft": {"model": {"code": "B738"}, "registration": "G-TAWX", "hex": "400ea1"}
    }
    with patch("tracker.aviation.enricher.AsyncSession") as mock_cls:
        mock_session = AsyncMock()
        mock_cls.return_value.__aenter__.return_value = mock_session
        mock_session.get = AsyncMock(return_value=mock_resp)
        result = await enrich_ids(["2b4e1f"])

    assert "2b4e1f" in result
    assert result["2b4e1f"] == ("B738", "G-TAWX", "400EA1")


async def test_enrich_ids_http_failure_excludes_flight_id():
    with patch("tracker.aviation.enricher.AsyncSession") as mock_cls:
        mock_session = AsyncMock()
        mock_cls.return_value.__aenter__.return_value = mock_session
        mock_session.get = AsyncMock(side_effect=Exception("timeout"))
        result = await enrich_ids(["2b4e1f"])

    assert "2b4e1f" not in result


async def test_enrich_ids_partial_failure_includes_only_successes():
    def side_effect(url, **kwargs):
        if "2b4e1f" in url:
            mock_resp = MagicMock()
            mock_resp.raise_for_status = MagicMock()
            mock_resp.json.return_value = {
                "aircraft": {"model": {"code": "B738"}, "registration": "G-TAWX", "hex": "400ea1"}
            }
            return mock_resp
        raise Exception("timeout")

    with patch("tracker.aviation.enricher.AsyncSession") as mock_cls:
        mock_session = AsyncMock()
        mock_cls.return_value.__aenter__.return_value = mock_session
        mock_session.get = AsyncMock(side_effect=side_effect)
        result = await enrich_ids(["2b4e1f", "deadbeef"])

    assert "2b4e1f" in result
    assert "deadbeef" not in result
