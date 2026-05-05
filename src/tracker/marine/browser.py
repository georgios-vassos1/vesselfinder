import re
from dataclasses import dataclass, field
from typing import Any

from playwright.async_api import async_playwright
from playwright_stealth import Stealth

from tracker.config import BROWSER_EXECUTABLES

Cookie = dict[str, Any]


@dataclass
class Session:
    cookies: list[Cookie]
    tile_url_template: str
    sample_tile_urls: list[str] = field(default_factory=list)


def _build_template(urls: list[str], fallback: str) -> str:
    if not urls:
        return fallback
    t = re.sub(r"/z:\d+", "/z:{z}", urls[0])
    t = re.sub(r"/X:\d+", "/X:{x}", t)
    t = re.sub(r"/Y:\d+", "/Y:{y}", t)
    return t


async def establish(
    os_name: str,
    url: str,
    url_pattern: re.Pattern[str],
    fallback_template: str,
) -> Session:
    browser_name, browser_path = BROWSER_EXECUTABLES[os_name]

    async with async_playwright() as p:
        browser = await p[browser_name].launch(
            executable_path=browser_path,
            headless=False,
            args=["--window-position=-32000,-32000"],
        )
        context = await browser.new_context()
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        captured_urls: list[str] = []
        page.on(
            "request",
            lambda req: captured_urls.append(req.url) if url_pattern.search(req.url) else None,
        )

        await page.goto(url)
        await page.wait_for_timeout(5000)

        cookies = await context.cookies()
        await browser.close()

    template = _build_template(captured_urls, fallback_template)
    return Session(cookies=cookies, tile_url_template=template, sample_tile_urls=captured_urls)
