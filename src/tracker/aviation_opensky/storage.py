from __future__ import annotations

import logging
from typing import Sequence

import psycopg

from tracker.aviation_opensky.models import Aircraft

log = logging.getLogger(__name__)

_DDL_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS aircraft_positions_opensky (
        captured_at   TIMESTAMPTZ      NOT NULL,
        icao24        TEXT             NOT NULL,
        callsign      TEXT,
        registration  TEXT,
        aircraft_type TEXT,
        lat           DOUBLE PRECISION,
        lon           DOUBLE PRECISION,
        altitude      INTEGER,
        on_ground     BOOLEAN,
        speed         INTEGER,
        heading       DOUBLE PRECISION,
        squawk        TEXT,
        last_contact  INTEGER
    )
    """,
    """
    SELECT create_hypertable(
        'aircraft_positions_opensky', 'captured_at',
        if_not_exists => TRUE
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS aircraft_positions_opensky_icao24
        ON aircraft_positions_opensky (icao24, captured_at DESC)
    """,
    """
    SELECT add_retention_policy(
        'aircraft_positions_opensky',
        INTERVAL '2 hours',
        if_not_exists => TRUE
    )
    """,
]

_COPY_SQL = """
COPY aircraft_positions_opensky (
    captured_at, icao24, callsign, registration, aircraft_type,
    lat, lon, altitude, on_ground, speed, heading, squawk, last_contact
) FROM STDIN
"""


def ensure_schema(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        for stmt in _DDL_STATEMENTS:
            cur.execute(stmt)
    conn.commit()
    log.info("OpenSky schema ready")


def insert_aircraft(conn: psycopg.Connection, aircraft: Sequence[Aircraft]) -> int:
    if not aircraft:
        return 0
    with conn.cursor() as cur:
        with cur.copy(_COPY_SQL) as copy:
            for a in aircraft:
                copy.write_row((
                    a.captured_at, a.icao24, a.callsign, a.registration,
                    a.aircraft_type, a.lat, a.lon, a.altitude, a.on_ground,
                    a.speed, a.heading, a.squawk, a.last_contact,
                ))
    conn.commit()
    return len(aircraft)
