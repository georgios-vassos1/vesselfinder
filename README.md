# vessel-tracker

Scrapes live vessel (AIS/MarineTraffic) and aircraft (ADS-B/FlightRadar24) positions and stores them in TimescaleDB for trajectory analysis.

## How it works

### Marine pipeline

1. **Session** — Playwright launches Chrome with stealth patches to pass Cloudflare, then extracts session cookies and the tile URL template from intercepted XHR requests.
2. **Tile fetch** — `curl_cffi` (Chrome TLS fingerprint) fetches all 208 maritime tiles at zoom:4 using the session cookies, concurrency-limited to 5.
3. **Normalise** — Raw JSON fields are cast to typed values (`SPEED` from tenths-of-knot to knots, coordinates to float, etc.) and a `captured_at` UTC timestamp is attached.
4. **Store** — Records are bulk-inserted into the `vessel_positions` hypertable via `COPY`.

### Aviation pipeline

1. **Fetch** — `curl_cffi` sends gRPC-Web requests to the FR24 LiveFeed API across a 20°×20° global grid (162 cells), concurrency-limited to 5.
2. **Decode** — Protobuf responses are decoded into `RawAircraftFields` structs (flight ID, lat/lon, altitude, speed, heading, on_ground, callsign).
3. **Normalise** — Fields are mapped to typed `Aircraft` objects with a `captured_at` UTC timestamp.
4. **Store** — Records are bulk-inserted into the `aircraft_positions` hypertable via `COPY`.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) — Python package manager
- [Docker](https://www.docker.com/) — for TimescaleDB
- Google Chrome at the default path (macOS: `/Applications/Google Chrome.app`, Linux: `/usr/bin/chromium`)

## Quick start

```bash
# 1. Install dependencies
uv sync --extra dev

# 2. Start TimescaleDB
make up

# 3. Set the database URL
export DATABASE_URL=postgresql://vessel:vessel@localhost:5432/vessel_track

# 4. Run the marine scraper
uv run vessel-tracker

# 5. Run the aviation scraper
uv run aviation-tracker
```

## Running with Docker

```bash
make up        # starts TimescaleDB + marine-scraper + aviation-scraper
make logs      # tail logs from both scrapers
make down      # stops everything
```

Both scraper containers connect to TimescaleDB automatically via the compose network. No `DATABASE_URL` export needed.

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | — | TimescaleDB connection string (required) |
| `SCRAPE_INTERVAL_MINUTES` | `10` | How often to run a full fetch |
| `SCRAPE_OS` | `Linux` | Browser executable profile for marine scraper (`MacOS` or `Linux`) |

## Database schema

### `vessel_positions` (hypertable, partitioned by `captured_at`)

| Column | Type | Notes |
|---|---|---|
| `captured_at` | `TIMESTAMPTZ` | UTC time of the scrape run |
| `ship_id` | `TEXT` | MarineTraffic vessel ID |
| `shipname` | `TEXT` | |
| `flag` | `TEXT` | ISO country code |
| `shiptype` | `SMALLINT` | MarineTraffic ship type code |
| `lat` / `lon` | `DOUBLE PRECISION` | Decimal degrees |
| `speed` | `REAL` | Knots |
| `course` | `REAL` | Degrees (0–360) |
| `heading` | `REAL` | Degrees (0–360) |
| `length` / `width` | `REAL` | Metres |
| `dwt` | `INTEGER` | Deadweight tonnage |
| `destination` | `TEXT` | Reported destination |
| `elapsed` | `INTEGER` | Seconds since last AIS update |

Index on `(ship_id, captured_at DESC)`.

### `aircraft_positions` (hypertable, partitioned by `captured_at`)

| Column | Type | Notes |
|---|---|---|
| `captured_at` | `TIMESTAMPTZ` | UTC time of the scrape run |
| `flight_id` | `TEXT` | FR24 flight ID (hex) |
| `callsign` | `TEXT` | ICAO ATC callsign e.g. `BAW71K` |
| `icao24` | `TEXT` | Mode-S hex address (lookup only) |
| `registration` | `TEXT` | Aircraft registration (lookup only) |
| `aircraft_type` | `TEXT` | ICAO type code e.g. `B738` (lookup only) |
| `origin` / `destination` | `TEXT` | IATA airport codes (lookup only) |
| `lat` / `lon` | `DOUBLE PRECISION` | Decimal degrees |
| `altitude` | `INTEGER` | Feet |
| `speed` | `INTEGER` | Knots (ground speed) |
| `heading` | `INTEGER` | Degrees (0–360) |
| `on_ground` | `BOOLEAN` | |
| `last_seen` | `INTEGER` | Unix timestamp from ADS-B message |

Index on `(flight_id, captured_at DESC)` and `(icao24, captured_at DESC)`.

### Example queries

```sql
-- Track a vessel over the last 24 hours
SELECT captured_at, lat, lon, speed, destination
FROM vessel_positions
WHERE ship_id = '7378535'
  AND captured_at > NOW() - INTERVAL '24 hours'
ORDER BY captured_at;

-- Track a flight over the last hour
SELECT captured_at, lat, lon, altitude, speed, on_ground
FROM aircraft_positions
WHERE callsign = 'BAW71K'
  AND captured_at > NOW() - INTERVAL '1 hour'
ORDER BY captured_at;

-- Vessels per flag in the latest snapshot
SELECT flag, COUNT(DISTINCT ship_id)
FROM vessel_positions
WHERE captured_at = (SELECT MAX(captured_at) FROM vessel_positions)
GROUP BY flag
ORDER BY count DESC;

-- Average speed by ship type over the past week
SELECT time_bucket('1 hour', captured_at) AS hour, gt_shiptype, AVG(speed)
FROM vessel_positions
WHERE captured_at > NOW() - INTERVAL '7 days'
  AND speed IS NOT NULL
GROUP BY hour, gt_shiptype
ORDER BY hour;
```

## Development

```bash
make lint         # ruff check
make test         # pytest
make clean-cache  # remove __pycache__, .venv, pytest/ruff caches
```
