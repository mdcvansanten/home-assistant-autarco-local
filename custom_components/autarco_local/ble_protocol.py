"""Small Modbus RTU codec, independent of Home Assistant and Bluetooth.

Solis BLE is a byte stream: notifications may fragment or combine RTU frames.
There is no transaction ID or echoed register address in a read response.
Only one request may be outstanding; a timeout must reset the connection.
"""

from __future__ import annotations


def crc16(data: bytes) -> bytes:
    """Return the Modbus CRC in wire order."""
    value = 0xFFFF
    for byte in data:
        value ^= byte
        for _ in range(8):
            value = (value >> 1) ^ (0xA001 if value & 1 else 0)
    return value.to_bytes(2, "little")


def read_request(function: int, address: int, count: int, unit: int = 0xFE) -> bytes:
    """Build an explicitly read-only request using absolute register addresses."""
    if function not in (3, 4):
        raise ValueError("Only holding/input register reads are supported")
    if not 0 <= address <= 65535 or not 1 <= count <= 125:
        raise ValueError("Invalid register address or count")
    if address + count > 65536 or not 1 <= unit <= 254:
        raise ValueError("Invalid register range or unit")
    body = bytes((unit, function)) + address.to_bytes(2, "big") + count.to_bytes(2, "big")
    return body + crc16(body)


class ModbusReadException(Exception):
    """A valid Modbus exception response, distinct from link failure."""

    def __init__(self, code: int) -> None:
        self.code = code
        super().__init__(f"Modbus exception 0x{code:02x}")


def decode_read(frame: bytes, function: int, count: int) -> list[int]:
    """Validate and unpack one CRC-checked response."""
    if len(frame) < 5 or crc16(frame[:-2]) != frame[-2:]:
        raise ValueError("Invalid Modbus CRC")
    if frame[1] == function | 0x80 and len(frame) == 5:
        raise ModbusReadException(frame[2])
    if frame[1] != function or frame[2] != count * 2 or len(frame) != count * 2 + 5:
        raise ValueError("Response does not match the requested function/count")
    return [int.from_bytes(frame[i:i + 2], "big") for i in range(3, len(frame) - 2, 2)]


class ReadFrameStream:
    """Recover complete, validated read responses from arbitrary BLE fragments."""

    def __init__(self, units: set[int]) -> None:
        self.units = units
        self.buffer = bytearray()
        self.dropped_bytes = 0

    def clear(self) -> None:
        self.buffer.clear()

    def feed(self, data: bytes) -> list[bytes]:
        self.buffer.extend(data)
        frames: list[bytes] = []
        # Search all offsets. A truncated-looking garbage prefix must not hide
        # a later complete frame with a valid CRC.
        while True:
            found = False
            for offset in range(max(0, len(self.buffer) - 2)):
                if self.buffer[offset] not in self.units:
                    continue
                function = self.buffer[offset + 1]
                count = self.buffer[offset + 2]
                if function in (0x83, 0x84):
                    length = 5
                elif function in (3, 4) and 2 <= count <= 250 and count % 2 == 0:
                    length = count + 5
                else:
                    continue
                if offset + length > len(self.buffer):
                    continue
                frame = bytes(self.buffer[offset:offset + length])
                if crc16(frame[:-2]) != frame[-2:]:
                    continue
                self.dropped_bytes += offset
                del self.buffer[:offset + length]
                frames.append(frame)
                found = True
                break
            if not found:
                break
        if len(self.buffer) > 512:
            removed = len(self.buffer) - 256
            self.dropped_bytes += removed
            del self.buffer[:removed]
        return frames
