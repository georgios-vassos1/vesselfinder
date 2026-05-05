import re

from tracker.browser import Session, establish
from tracker.marine.config import FALLBACK_TILE_TEMPLATE, MARINETRAFFIC_URL
from tracker.marine.fetcher import _DEFAULT_ZOOM, fetch_all

_AIS_URL_PATTERN = re.compile(
    re.escape("/get_data_json_4/z:") + r"\d+/X:\d+/Y:\d+/station:0"
)


def _filter_ais_urls(requests: list) -> list[str]:
    return [r.url for r in requests if _AIS_URL_PATTERN.search(r.url)]


async def establish_session(os_name: str = "MacOS") -> Session:
    return await establish(
        os_name=os_name,
        url=MARINETRAFFIC_URL,
        url_pattern=_AIS_URL_PATTERN,
        fallback_template=FALLBACK_TILE_TEMPLATE,
    )


async def client(
    os_name: str = "MacOS",
    zoom: int = _DEFAULT_ZOOM,
) -> list[dict]:
    session = await establish_session(os_name=os_name)
    return await fetch_all(session.tile_url_template, session.cookies, zoom=zoom)
