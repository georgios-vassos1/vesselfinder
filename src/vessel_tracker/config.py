MARINETRAFFIC_URL = (
    "https://www.marinetraffic.com/en/ais/home/centerx:22.1/centery:10.0/zoom:2"
)

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 "
        "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.11"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.3",
    "Accept-Encoding": "none",
    "Accept-Language": "en-US,en;q=0.8",
    "Connection": "keep-alive",
}

BROWSER_EXECUTABLES = {
    "MacOS": ("chromium", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    "Linux": ("chromium", "/usr/bin/chromium"),
}
