from vessel_tracker.ais_data_scraper import _AIS_URL_PATTERN, _filter_ais_urls
from vessel_tracker.tile_fetcher import tile_urls


class _FakeRequest:
    def __init__(self, url: str):
        self.url = url


def test_ais_url_pattern_matches_valid():
    url = "https://www.marinetraffic.com/get_data_json_4/z:3/X:4/Y:2/station:0"
    assert _AIS_URL_PATTERN.search(url)


def test_ais_url_pattern_rejects_other():
    url = "https://www.marinetraffic.com/en/ais/home"
    assert not _AIS_URL_PATTERN.search(url)


def test_filter_ais_urls_returns_only_matching():
    requests = [
        _FakeRequest("https://www.marinetraffic.com/get_data_json_4/z:3/X:4/Y:2/station:0"),
        _FakeRequest("https://www.marinetraffic.com/en/ais/home"),
        _FakeRequest("https://www.marinetraffic.com/get_data_json_4/z:10/X:512/Y:300/station:0"),
    ]
    result = _filter_ais_urls(requests)
    assert len(result) == 2
    assert all("get_data_json_4" in url for url in result)


def test_tile_urls_zoom_2():
    template = "https://example.com/z:{z}/X:{x}/Y:{y}"
    urls = tile_urls(template, zoom=2)
    # All 16 tiles pass the lat filter at zoom:2 (Arctic tiles are large, min lat still below 74)
    assert len(urls) == 16
    assert all("z:2" in u for u in urls)
    assert len(set(urls)) == 16


def test_tile_urls_zoom_4():
    template = "https://example.com/z:{z}/X:{x}/Y:{y}"
    urls = tile_urls(template, zoom=4)
    # 256 total minus ~48 Arctic tiles filtered above 74°N
    assert len(urls) == 208
    assert all("z:4" in u for u in urls)
    assert len(set(urls)) == 208


def test_tile_urls_excludes_arctic():
    template = "https://example.com/z:{z}/X:{x}/Y:{y}"
    urls = tile_urls(template, zoom=4)
    # Y:0 tiles (lat 82-85°N) should all be excluded
    assert not any("X:0/Y:0" in u for u in urls)
    assert not any("X:8/Y:0" in u for u in urls)
