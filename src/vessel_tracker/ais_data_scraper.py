import re

from vessel_tracker.session import Session, establish
from vessel_tracker.tile_fetcher import _DEFAULT_ZOOM, fetch_all

# Kept here for backwards compatibility — tests and scripts import from this module.
_AIS_URL_PATTERN = re.compile(
    re.escape("/get_data_json_4/z:") + r"\d+/X:\d+/Y:\d+/station:0"
)


def _filter_ais_urls(requests: list) -> list[str]:
    return [r.url for r in requests if _AIS_URL_PATTERN.search(r.url)]


async def client(
    os_name: str = "MacOS",
    zoom: int = _DEFAULT_ZOOM,
) -> list[dict]:
    session: Session = await establish(os_name=os_name)
    return await fetch_all(session.tile_url_template, session.cookies, zoom=zoom)
