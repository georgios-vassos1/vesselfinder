from typing import Any, Optional


def to_str(value: Any) -> Optional[str]:
    s = str(value).strip() if value is not None else None
    return s if s else None


def to_float(value: Any) -> Optional[float]:
    try:
        return float(value) if value is not None else None
    except (ValueError, TypeError):
        return None


def to_int(value: Any) -> Optional[int]:
    try:
        return int(value) if value is not None else None
    except (ValueError, TypeError):
        return None
