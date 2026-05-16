from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Iterator


@dataclass
class RawAircraftFields:
    flight_id: int = 0
    lat: float | None = None
    lon: float | None = None
    heading: int | None = None
    altitude: int | None = None
    speed: int | None = None
    last_seen: int | None = None
    on_ground: bool | None = None
    callsign: str | None = None


def _varint(value: int) -> bytes:
    result = []
    while value > 0x7F:
        result.append((value & 0x7F) | 0x80)
        value >>= 7
    result.append(value & 0x7F)
    return bytes(result)


def _length_delimited(field_num: int, data: bytes) -> bytes:
    return bytes([field_num << 3 | 2]) + _varint(len(data)) + data


def _float32_field(field_num: int, value: float) -> bytes:
    return bytes([field_num << 3 | 5]) + struct.pack("<f", value)


# Constant filter bytes extracted from a captured browser request.
_FILTERS = bytes.fromhex(
    "0a0b000102030405060708090a"
    "120c000102030405060708090a0b"
    "1803"
)

_TAIL = bytes.fromhex("300138ac0240c07048005200")


def encode_request(north: float, south: float, west: float, east: float) -> bytes:
    bounds = (
        _float32_field(1, north)
        + _float32_field(2, south)
        + _float32_field(3, west)
        + _float32_field(4, east)
    )
    payload = (
        _length_delimited(1, bounds)
        + _length_delimited(2, _FILTERS)
        + _TAIL
    )
    return b"\x00" + struct.pack(">I", len(payload)) + payload


def _read_varint(data: bytes, pos: int) -> tuple[int, int]:
    result, shift = 0, 0
    while True:
        b = data[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return result, pos


def decode_response(body: bytes) -> Iterator[RawAircraftFields]:
    if len(body) < 5:
        return
    msg_len = struct.unpack(">I", body[1:5])[0]
    pos, end = 5, min(5 + msg_len, len(body))

    while pos < end:
        tag, pos = _read_varint(body, pos)
        field_num, wire_type = tag >> 3, tag & 7

        if wire_type == 2:
            length, pos = _read_varint(body, pos)
            msg_end = pos + length
            if field_num == 1:
                yield _decode_aircraft(body, pos, msg_end)
            pos = msg_end
        elif wire_type == 0:
            _, pos = _read_varint(body, pos)
        elif wire_type == 5:
            pos += 4
        elif wire_type == 1:
            pos += 8
        else:
            break


def _decode_aircraft(data: bytes, start: int, end: int) -> RawAircraftFields:
    pos = start
    raw = RawAircraftFields()
    while pos < end:
        if pos >= len(data):
            break
        tag, pos = _read_varint(data, pos)
        field_num, wire_type = tag >> 3, tag & 7

        if wire_type == 0:
            val, pos = _read_varint(data, pos)
            if field_num == 1:
                raw.flight_id = val
            elif field_num == 4:
                raw.heading = val
            elif field_num == 5:
                raw.altitude = val
            elif field_num == 6:
                raw.speed = val
            elif field_num == 9:
                raw.last_seen = val
            elif field_num == 10:
                raw.on_ground = bool(val)
        elif wire_type == 2:
            length, pos = _read_varint(data, pos)
            raw_bytes = data[pos:pos + length]
            if field_num == 11:
                try:
                    s = raw_bytes.decode("utf-8")
                    raw.callsign = s if all(c.isprintable() for c in s) else None
                except Exception:
                    pass
            pos += length
        elif wire_type == 5:
            val_f = struct.unpack_from("<f", data, pos)[0]
            if field_num == 2:
                raw.lat = val_f
            elif field_num == 3:
                raw.lon = val_f
            pos += 4
        elif wire_type == 1:
            pos += 8
        else:
            break

    return raw
