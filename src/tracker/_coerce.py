from __future__ import annotations

from typing import Any


def to_str(value: Any) -> str | None:
    s = str(value).strip() if value is not None else None
    return s if s else None


def to_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (ValueError, TypeError):
        return None


def to_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (ValueError, TypeError):
        return None
