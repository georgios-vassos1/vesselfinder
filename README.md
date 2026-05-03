# vessel-tracker

Scrapes global AIS vessel position data from MarineTraffic and stores it in TimescaleDB for trajectory analysis.

Each run fetches ~32,000 unique vessels across 208 world tiles (zoom level 4, Arctic tiles excluded), deduplicates by `SHIP_ID`, normalises fields, and inserts a timestamped snapshot into the database. Running every 10 minutes builds a continuous position history across all active vessels.

## How it works

1. **Session** — Playwright launches Chrome with stealth patches to pass Cloudflare, then extracts session cookies and the tile URL template from intercepted XHR requests.
2. **Tile fetch** — Direct `curl_cffi` requests (impersonating Chrome's TLS fingerprint) are made to all 208 maritime tiles at zoom:4 using the session cookies, with a concurrency limit of 5 to avoid rate limiting.
3. **Normalise** — Raw API fields are cast to typed values (`SPEED` from tenths-of-knot to knots, `LAT`/`LON` to float, etc.) and a `captured_at` UTC timestamp is attached.
4. **Store** — Normalised records are bulk-inserted into the `vessel_positions` hypertable in TimescaleDB.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) — Python package manager
- [Docker](https://www.docker.com/) — for TimescaleDB
- Google Chrome installed at the default path (macOS: `/Applications/Google Chrome.app`)

## Quick start

```bash
# 1. Install dependencies
uv sync --extra dev

# 2. Start TimescaleDB
make up

# 3. Set the database URL
export DATABASE_URL=postgresql://vessel:vessel@localhost:5432/vessel_track

# 4. Run a single fetch and validate coverage
uv run python scripts/fetch_all_vessels.py

# 5. Start the continuous scraper loop (10-min interval)
uv run vessel-tracker
```

## Running with Docker

```bash
make up        # starts TimescaleDB + scraper container
make down      # stops everything
```

The scraper container connects to TimescaleDB automatically via the compose network. No `DATABASE_URL` export needed.

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | — | TimescaleDB connection string (required) |
| `SCRAPE_INTERVAL_MINUTES` | `10` | How often to run a full fetch |
| `SCRAPE_OS` | `Linux` | Browser executable profile (`MacOS` or `Linux`) |

## Database schema

Table: `vessel_positions` (TimescaleDB hypertable, partitioned by `captured_at`)

| Column | Type | Notes |
|---|---|---|
| `captured_at` | `TIMESTAMPTZ` | UTC time of the scrape run |
| `ship_id` | `TEXT` | MarineTraffic vessel ID |
| `shipname` | `TEXT` | |
| `flag` | `CHAR(2)` | ISO country code |
| `shiptype` | `SMALLINT` | MarineTraffic ship type code |
| `lat` / `lon` | `DOUBLE PRECISION` | Decimal degrees |
| `speed` | `REAL` | Knots |
| `course` | `REAL` | Degrees (0–360) |
| `heading` | `REAL` | Degrees (0–360) |
| `length` / `width` | `REAL` | Metres |
| `dwt` | `INTEGER` | Deadweight tonnage |
| `destination` | `TEXT` | Reported destination |
| `elapsed` | `INTEGER` | Seconds since last AIS update |

Index on `(ship_id, captured_at DESC)` for efficient per-vessel trajectory queries.

### Example queries

```sql
-- Track a specific vessel over the last 24 hours
SELECT captured_at, lat, lon, speed, destination
FROM vessel_positions
WHERE ship_id = '7378535'
  AND captured_at > NOW() - INTERVAL '24 hours'
ORDER BY captured_at;

-- Vessels per flag in the last snapshot
SELECT flag, COUNT(DISTINCT ship_id)
FROM vessel_positions
WHERE captured_at = (SELECT MAX(captured_at) FROM vessel_positions)
GROUP BY flag
ORDER BY count DESC;

-- Average speed by ship type over the past week (time_bucket)
SELECT time_bucket('1 hour', captured_at) AS hour, gt_shiptype, AVG(speed)
FROM vessel_positions
WHERE captured_at > NOW() - INTERVAL '7 days'
  AND speed IS NOT NULL
GROUP BY hour, gt_shiptype
ORDER BY hour;
```

## Development

```bash
make lint      # ruff check
make test      # pytest
make clean-cache  # remove __pycache__, .venv, pytest/ruff caches
```
