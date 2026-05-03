import re
from dataclasses import dataclass, field

from playwright.async_api import async_playwright
from playwright_stealth import Stealth

from vessel_tracker.config import BROWSER_EXECUTABLES, MARINETRAFFIC_URL

_AIS_URL_PATTERN = re.compile(
    re.escape("/get_data_json_4/z:") + r"\d+/X:\d+/Y:\d+/station:0"
)


@dataclass
class Session:
    cookies: list[dict]
    tile_url_template: str
    # Captured during page load — useful for debugging but not required for fetching
    sample_tile_urls: list[str] = field(default_factory=list)


def _build_template(urls: list[str]) -> str:
    if not urls:
        return "https://www.marinetraffic.com/getData/get_data_json_4/z:{z}/X:{x}/Y:{y}/station:0"
    t = re.sub(r"/z:\d+", "/z:{z}", urls[0])
    t = re.sub(r"/X:\d+", "/X:{x}", t)
    t = re.sub(r"/Y:\d+", "/Y:{y}", t)
    return t


async def establish(os_name: str = "MacOS", headless: bool = False) -> Session:
    browser_name, browser_path = BROWSER_EXECUTABLES[os_name]

    async with async_playwright() as p:
        browser = await p[browser_name].launch(executable_path=browser_path, headless=headless)
        context = await browser.new_context()

        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        ais_urls: list[str] = []
        page.on(
            "request",
            lambda req: ais_urls.append(req.url) if _AIS_URL_PATTERN.search(req.url) else None,
        )

        await page.goto(MARINETRAFFIC_URL)
        await page.wait_for_timeout(5000)

        cookies = await context.cookies()
        await browser.close()

    template = _build_template(ais_urls)
    return Session(cookies=cookies, tile_url_template=template, sample_tile_urls=ais_urls)
