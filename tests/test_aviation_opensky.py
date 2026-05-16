import json

from tracker.aviation.opensky import load


def test_load_returns_empty_dict_for_missing_file(tmp_path):
    assert load(tmp_path / "missing.json") == {}


def test_load_returns_icao24_keyed_dict(tmp_path):
    path = tmp_path / "opensky.json"
    path.write_text(json.dumps({"400EA1": {"type": "B738", "registration": "G-TAWX"}}))
    assert load(path) == {"400EA1": ("B738", "G-TAWX")}


def test_load_handles_null_fields(tmp_path):
    path = tmp_path / "opensky.json"
    path.write_text(json.dumps({"400EA1": {"type": None, "registration": None}}))
    assert load(path) == {"400EA1": (None, None)}


def test_load_multiple_entries(tmp_path):
    path = tmp_path / "opensky.json"
    path.write_text(json.dumps({
        "400EA1": {"type": "B738", "registration": "G-TAWX"},
        "3C6445": {"type": "A320", "registration": "F-GKXA"},
    }))
    result = load(path)
    assert len(result) == 2
    assert result["3C6445"] == ("A320", "F-GKXA")
