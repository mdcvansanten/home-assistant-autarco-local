#!/usr/bin/env python3
"""Standalone read-only probe for the user's existing Bleak virtualenv.

Keep HA's BLE transport paused and the Solis app disconnected while running.
No Home Assistant dependencies, credentials, writes or packet sniffing.
"""

import argparse
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from bleak import BleakClient, BleakScanner

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "autarco_local"))
from ble_protocol import ModbusReadException, ReadFrameStream, decode_read, read_request
from const import BLE_RUNTIME_BLOCKS, SETTING_REGISTER_BLOCKS

TX = "0000ffe1-0000-1000-8000-00805f9b34fb"
RX = "0000ffe2-0000-1000-8000-00805f9b34fb"


async def probe(args):
    device = await BleakScanner.find_device_by_address(args.address, timeout=20)
    if device is None:
        raise RuntimeError("Omvormer niet gevonden. Controleer bereik en verbreek andere BLE-verbindingen.")
    stream = ReadFrameStream({1, 254})
    pending = None
    expected = None

    def receive(_sender, data):
        for frame in stream.feed(bytes(data)):
            if pending is not None and not pending.done() and expected is not None:
                function, count = expected
                if frame[1] == function | 0x80 or (frame[1] == function and frame[2] == count * 2):
                    pending.set_result(frame)

    results = []
    async with BleakClient(device, timeout=30) as client:
        await client.start_notify(RX, receive)

        async def read(function, start, count):
            nonlocal pending, expected
            stream.clear()
            pending = asyncio.get_running_loop().create_future()
            expected = (function, count)
            try:
                async with asyncio.timeout(8):
                    await client.write_gatt_char(TX, read_request(function, start, count), response=False)
                    frame = await pending
                return decode_read(frame, function, count)
            finally:
                if pending is not None and not pending.done():
                    pending.cancel()
                pending = None; expected = None

        async def read_blocks(function, blocks):
            registers = {}; unsupported = []
            async def one(start, count):
                try:
                    values = await read(function, start, count)
                except ModbusReadException as err:
                    if err.code == 2 and count > 1:
                        half = count // 2
                        await one(start, half); await one(start + half, count - half)
                        return
                    if err.code in (1, 2):
                        unsupported.append({"start": start, "count": count, "exception": err.code})
                        return
                    raise
                registers.update({str(start + offset): value for offset, value in enumerate(values)})
                await asyncio.sleep(0.03)
            for start, count in blocks:
                await one(start, count)
            return registers, unsupported

        for poll in range(args.polls):
            started = datetime.now(timezone.utc)
            # Start each snapshot with the physically confirmed single-register
            # temperature read. A transport timeout aborts the whole probe so a
            # delayed RTU response can never be assigned to the next request.
            temperature = (await read(4, 33093, 1))[0]
            if temperature >= 32768:
                temperature -= 65536
            runtime, unsupported = await read_blocks(4, BLE_RUNTIME_BLOCKS)
            settings, unsupported_settings = await read_blocks(3, SETTING_REGISTER_BLOCKS) if poll == 0 else ({}, [])
            result = {
                "started_at": started.isoformat(),
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "poll": poll + 1, "temperature_c": temperature / 10,
                "runtime_raw": runtime, "settings_raw": settings,
                "unsupported_runtime": unsupported,
                "unsupported_settings": unsupported_settings,
                "transport": "ble", "read_only": True,
                "response_unit": 1, "request_unit": 254,
            }
            results.append(result)
            print(json.dumps(result, ensure_ascii=False), flush=True)
            if poll + 1 < args.polls:
                await asyncio.sleep(args.interval)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--address", required=True)
    parser.add_argument("--polls", type=int, default=5)
    parser.add_argument("--interval", type=float, default=5)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not 1 <= args.polls <= 100 or not 1 <= args.interval <= 3600:
        parser.error("Gebruik 1–100 polls en een interval van 1–3600 seconden")
    try:
        result = asyncio.run(probe(args))
    except Exception as err:
        print(f"FOUT: {type(err).__name__}: {err}", file=sys.stderr)
        return 1
    if args.output:
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
        print(f"Rapport: {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
