FR24_GRPC_URL = "https://data-feed.flightradar24.com/fr24.feed.api.v1.Feed/LiveFeed"

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.flightradar24.com/",
    "fr24-platform": "web-26.125.1047",
    "x-envoy-retry-grpc-on": "unavailable",
    "content-type": "application/grpc-web+proto",
    "x-grpc-web": "1",
    "x-user-agent": "grpc-web-javascript/0.1",
}
