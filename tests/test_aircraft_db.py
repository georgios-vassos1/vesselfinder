import json

from tracker.aviation.aircraft_db import load, save


def test_load_returns_empty_dict_for_missing_file(tmp_path):
    assert load(tmp_path / "missing.json") == {}


def test_load_returns_entries_keyed_by_flight_id(tmp_path):
    path = tmp_path / "db.json"
    path.write_text(json.dumps({
        "3fb7d4d2": {"type": "B789", "registration": "CC-BGK", "icao24": "E80451"},
    }))
    assert load(path) == {"3fb7d4d2": ("B789", "CC-BGK", "E80451")}


def test_load_handles_null_fields(tmp_path):
    path = tmp_path / "db.json"
    path.write_text(json.dumps({
        "3fb7d4d2": {"type": None, "registration": None, "icao24": "E80451"},
    }))
    assert load(path) == {"3fb7d4d2": (None, None, "E80451")}


def test_save_creates_file_with_entry(tmp_path):
    path = tmp_path / "db.json"
    save({"3fb7d4d2": ("B789", "CC-BGK", "E80451")}, path)
    data = json.loads(path.read_text())
    assert data["3fb7d4d2"] == {"type": "B789", "registration": "CC-BGK", "icao24": "E80451"}


def test_save_merges_with_existing_entries(tmp_path):
    path = tmp_path / "db.json"
    path.write_text(json.dumps({"3fb7d4d2": {"type": "B789", "registration": "CC-BGK", "icao24": "E80451"}}))
    save({"3fb8e78f": ("A20N", "CC-BHK", "E80488")}, path)
    data = json.loads(path.read_text())
    assert "3fb7d4d2" in data
    assert "3fb8e78f" in data


def test_save_overwrites_existing_entry(tmp_path):
    path = tmp_path / "db.json"
    path.write_text(json.dumps({"3fb7d4d2": {"type": None, "registration": None, "icao24": "E80451"}}))
    save({"3fb7d4d2": ("B789", "CC-BGK", "E80451")}, path)
    data = json.loads(path.read_text())
    assert data["3fb7d4d2"]["type"] == "B789"
