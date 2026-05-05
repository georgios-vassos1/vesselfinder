import logging
from typing import Sequence

import psycopg

from tracker.marine.models import Vessel

log = logging.getLogger(__name__)

_DDL_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS vessel_positions (
        captured_at TIMESTAMPTZ      NOT NULL,
        ship_id     TEXT             NOT NULL,
        shipname    TEXT,
        flag        TEXT,
        shiptype    SMALLINT,
        gt_shiptype SMALLINT,
        type_name   TEXT,
        status_name TEXT,
        lat         DOUBLE PRECISION,
        lon         DOUBLE PRECISION,
        speed       REAL,
        course      REAL,
        heading     REAL,
        rot         REAL,
        length      REAL,
        width       REAL,
        l_fore      REAL,
        w_left      REAL,
        dwt         INTEGER,
        destination TEXT,
        elapsed     INTEGER
    )
    """,
    """
    SELECT create_hypertable(
        'vessel_positions', 'captured_at',
        if_not_exists => TRUE
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS vessel_positions_ship_id
        ON vessel_positions (ship_id, captured_at DESC)
    """,
]

_COPY_SQL = """
COPY vessel_positions (
    captured_at, ship_id, shipname, flag, shiptype, gt_shiptype,
    type_name, status_name, lat, lon, speed, course, heading, rot,
    length, width, l_fore, w_left, dwt, destination, elapsed
) FROM STDIN
"""


def ensure_schema(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        for stmt in _DDL_STATEMENTS:
            cur.execute(stmt)
    conn.commit()
    log.info("Schema ready")


def insert_vessels(conn: psycopg.Connection, vessels: Sequence[Vessel]) -> int:
    if not vessels:
        return 0

    with conn.cursor() as cur:
        with cur.copy(_COPY_SQL) as copy:
            for v in vessels:
                copy.write_row((
                    v.captured_at, v.ship_id, v.shipname, v.flag,
                    v.shiptype, v.gt_shiptype, v.type_name, v.status_name,
                    v.lat, v.lon, v.speed, v.course, v.heading, v.rot,
                    v.length, v.width, v.l_fore, v.w_left,
                    v.dwt, v.destination, v.elapsed,
                ))
    conn.commit()
    return len(vessels)
