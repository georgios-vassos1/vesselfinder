from tracker.marine.fetcher import tile_urls
from tracker.marine.scraper import _AIS_URL_PATTERN


def test_ais_url_pattern_matches_valid():
    url = "https://www.marinetraffic.com/get_data_json_4/z:3/X:4/Y:2/station:0"
    assert _AIS_URL_PATTERN.search(url)


def test_ais_url_pattern_rejects_other():
    url = "https://www.marinetraffic.com/en/ais/home"
    assert not _AIS_URL_PATTERN.search(url)


def test_tile_urls_zoom_2():
    template = "https://example.com/z:{z}/X:{x}/Y:{y}"
    urls = tile_urls(template, zoom=2)
    assert len(urls) == 16
    assert all("z:2" in u for u in urls)
    assert len(set(urls)) == 16


def test_tile_urls_zoom_4():
    template = "https://example.com/z:{z}/X:{x}/Y:{y}"
    urls = tile_urls(template, zoom=4)
    assert len(urls) == 208
    assert all("z:4" in u for u in urls)
    assert len(set(urls)) == 208


def test_tile_urls_excludes_arctic():
    template = "https://example.com/z:{z}/X:{x}/Y:{y}"
    urls = tile_urls(template, zoom=4)
    assert not any("X:0/Y:0" in u for u in urls)
    assert not any("X:8/Y:0" in u for u in urls)
