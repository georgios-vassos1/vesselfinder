from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Required, TypedDict

from tracker._coerce import to_float, to_int, to_str


class AISRecord(TypedDict, total=False):
    SHIP_ID: Required[str]
    SHIPNAME: str
    FLAG: str
    SHIPTYPE: str
    GT_SHIPTYPE: str
    TYPE_NAME: str
    STATUS_NAME: str
    LAT: str
    LON: str
    SPEED: str
    COURSE: str
    HEADING: str
    ROT: str
    LENGTH: str
    WIDTH: str
    L_FORE: str
    W_LEFT: str
    DWT: str
    DESTINATION: str
    ELAPSED: str


@dataclass
class Vessel:
    # Identity
    ship_id: str
    shipname: str | None
    flag: str | None
    shiptype: int | None
    gt_shiptype: int | None
    type_name: str | None
    status_name: str | None

    # Position
    lat: float | None
    lon: float | None

    # Movement
    speed: float | None       # knots
    course: float | None      # degrees (0–360)
    heading: float | None     # degrees (0–360)
    rot: float | None

    # Dimensions
    length: float | None      # metres
    width: float | None       # metres
    l_fore: float | None
    w_left: float | None
    dwt: int | None

    # Voyage
    destination: str | None
    elapsed: int | None       # seconds since last AIS update

    # Capture
    captured_at: datetime

    @classmethod
    def from_raw(cls, raw: AISRecord, captured_at: datetime) -> Vessel:
        speed_raw = to_float(raw.get("SPEED"))
        speed = round(speed_raw / 10, 1) if speed_raw is not None else None

        return cls(
            ship_id=raw["SHIP_ID"],
            shipname=to_str(raw.get("SHIPNAME")),
            flag=to_str(raw.get("FLAG")),
            shiptype=to_int(raw.get("SHIPTYPE")),
            gt_shiptype=to_int(raw.get("GT_SHIPTYPE")),
            type_name=to_str(raw.get("TYPE_NAME")),
            status_name=to_str(raw.get("STATUS_NAME")),
            lat=to_float(raw.get("LAT")),
            lon=to_float(raw.get("LON")),
            speed=speed,
            course=to_float(raw.get("COURSE")),
            heading=to_float(raw.get("HEADING")),
            rot=to_float(raw.get("ROT")),
            length=to_float(raw.get("LENGTH")),
            width=to_float(raw.get("WIDTH")),
            l_fore=to_float(raw.get("L_FORE")),
            w_left=to_float(raw.get("W_LEFT")),
            dwt=to_int(raw.get("DWT")),
            destination=to_str(raw.get("DESTINATION")),
            elapsed=to_int(raw.get("ELAPSED")),
            captured_at=captured_at,
        )
