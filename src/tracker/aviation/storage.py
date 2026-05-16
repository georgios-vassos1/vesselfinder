import logging
from datetime import datetime, timezone
from typing import Sequence

import psycopg
from psycopg.rows import dict_row

from tracker.aviation.models import Aircraft

log = logging.getLogger(__name__)

_ENRICHMENT_DDL = """
CREATE TABLE IF NOT EXISTS aircraft_enrichment (
    flight_id   TEXT PRIMARY KEY,
    icao24      TEXT NOT NULL,
    enriched_at TIMESTAMPTZ NOT NULL
)
"""

_DDL_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS aircraft_positions (
        captured_at   TIMESTAMPTZ   NOT NULL,
        flight_id     TEXT          NOT NULL,
        icao24        TEXT,
        callsign      TEXT,
        flight_number TEXT,
        registration  TEXT,
        aircraft_type TEXT,
        origin        TEXT,
        destination   TEXT,
        lat           DOUBLE PRECISION,
        lon           DOUBLE PRECISION,
        altitude      INTEGER,
        on_ground     BOOLEAN,
        speed         INTEGER,
        heading       INTEGER,
        vspeed        INTEGER,
        squawk        TEXT,
        last_seen     INTEGER
    )
    """,
    """
    SELECT create_hypertable(
        'aircraft_positions', 'captured_at',
        if_not_exists => TRUE
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS aircraft_positions_flight_id
        ON aircraft_positions (flight_id, captured_at DESC)
    """,
    """
    CREATE INDEX IF NOT EXISTS aircraft_positions_icao24
        ON aircraft_positions (icao24, captured_at DESC)
    """,
    """
    SELECT add_retention_policy(
        'aircraft_positions',
        INTERVAL '2 hours',
        if_not_exists => TRUE
    )
    """,
]

_COPY_SQL = """
COPY aircraft_positions (
    captured_at, flight_id, icao24, callsign, flight_number,
    registration, aircraft_type, origin, destination,
    lat, lon, altitude, on_ground, speed, heading, vspeed, squawk, last_seen
) FROM STDIN
"""


def ensure_schema(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        for stmt in _DDL_STATEMENTS:
            cur.execute(stmt)
        cur.execute(_ENRICHMENT_DDL)
    conn.commit()
    log.info("Aviation schema ready")


def load_enrichment(
    conn: psycopg.Connection,
    flight_ids: list[str],
) -> dict[str, str]:
    if not flight_ids:
        return {}
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT flight_id, icao24 FROM aircraft_enrichment WHERE flight_id = ANY(%s)",
            (flight_ids,),
        )
        return {row["flight_id"]: row["icao24"] for row in cur.fetchall()}


def store_enrichment(
    conn: psycopg.Connection,
    enrichments: dict[str, str],
) -> None:
    if not enrichments:
        return
    now = datetime.now(timezone.utc)
    with conn.cursor() as cur:
        for flight_id, icao24 in enrichments.items():
            cur.execute(
                """
                INSERT INTO aircraft_enrichment (flight_id, icao24, enriched_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (flight_id) DO NOTHING
                """,
                (flight_id, icao24, now),
            )
    conn.commit()


def insert_aircraft(conn: psycopg.Connection, aircraft: Sequence[Aircraft]) -> int:
    if not aircraft:
        return 0

    with conn.cursor() as cur:
        with cur.copy(_COPY_SQL) as copy:
            for a in aircraft:
                copy.write_row((
                    a.captured_at, a.flight_id, a.icao24, a.callsign,
                    a.flight_number, a.registration, a.aircraft_type,
                    a.origin, a.destination,
                    a.lat, a.lon, a.altitude, a.on_ground,
                    a.speed, a.heading, a.vspeed, a.squawk, a.last_seen,
                ))
    conn.commit()
    return len(aircraft)
