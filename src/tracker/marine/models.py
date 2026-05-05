from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


def _float(value) -> Optional[float]:
    try:
        return float(value) if value is not None else None
    except (ValueError, TypeError):
        return None


def _int(value) -> Optional[int]:
    try:
        return int(value) if value is not None else None
    except (ValueError, TypeError):
        return None


def _str(value) -> Optional[str]:
    """Return None for missing or blank strings."""
    s = str(value).strip() if value is not None else None
    return s if s else None


@dataclass
class Vessel:
    # Identity
    ship_id: str
    shipname: Optional[str]
    flag: Optional[str]
    shiptype: Optional[int]
    gt_shiptype: Optional[int]
    type_name: Optional[str]
    status_name: Optional[str]

    # Position
    lat: Optional[float]
    lon: Optional[float]

    # Movement
    speed: Optional[float]        # knots
    course: Optional[float]       # degrees (0–360)
    heading: Optional[float]      # degrees (0–360)
    rot: Optional[float]

    # Dimensions
    length: Optional[float]       # metres
    width: Optional[float]        # metres
    l_fore: Optional[float]
    w_left: Optional[float]
    dwt: Optional[int]

    # Voyage
    destination: Optional[str]
    elapsed: Optional[int]        # seconds since last AIS update

    # Capture
    captured_at: datetime

    @classmethod
    def from_raw(cls, raw: dict) -> Vessel:
        captured_at_raw = raw.get("captured_at")
        if isinstance(captured_at_raw, str):
            captured_at = datetime.fromisoformat(captured_at_raw)
        else:
            captured_at = datetime.now(timezone.utc)

        speed_raw = _float(raw.get("SPEED"))
        speed = round(speed_raw / 10, 1) if speed_raw is not None else None

        return cls(
            ship_id=raw["SHIP_ID"],
            shipname=_str(raw.get("SHIPNAME")),
            flag=_str(raw.get("FLAG")),
            shiptype=_int(raw.get("SHIPTYPE")),
            gt_shiptype=_int(raw.get("GT_SHIPTYPE")),
            type_name=_str(raw.get("TYPE_NAME")),
            status_name=_str(raw.get("STATUS_NAME")),
            lat=_float(raw.get("LAT")),
            lon=_float(raw.get("LON")),
            speed=speed,
            course=_float(raw.get("COURSE")),
            heading=_float(raw.get("HEADING")),
            rot=_float(raw.get("ROT")),
            length=_float(raw.get("LENGTH")),
            width=_float(raw.get("WIDTH")),
            l_fore=_float(raw.get("L_FORE")),
            w_left=_float(raw.get("W_LEFT")),
            dwt=_int(raw.get("DWT")),
            destination=_str(raw.get("DESTINATION")),
            elapsed=_int(raw.get("ELAPSED")),
            captured_at=captured_at,
        )
