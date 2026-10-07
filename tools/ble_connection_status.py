#!/usr/bin/env python3
"""Read current BlueZ connection state without scanning or connecting."""

import argparse
import asyncio
import re
import sys


def _value(properties, name, default=None):
    value = properties.get(name)
    return getattr(value, "value", value) if value is not None else default


def status_lines(objects, address):
    """Report only Bluetooth adapters and the requested inverter device."""
    address = address.upper()
    lines = [f"Omvormer: {address}"]
    for path, interfaces in sorted(objects.items()):
        adapter = interfaces.get("org.bluez.Adapter1")
        if adapter is not None:
            powered = "yes" if _value(adapter, "Powered", False) else "no"
            scanning = "yes" if _value(adapter, "Discovering", False) else "no"
            lines.append(f"Adapter {path.rsplit('/', 1)[-1]}: Powered={powered}, Discovering={scanning}")
    found = False
    for path, interfaces in sorted(objects.items()):
        device = interfaces.get("org.bluez.Device1")
        if device is None or str(_value(device, "Address", "")).upper() != address:
            continue
        found = True
        adapter = str(_value(device, "Adapter", path.rsplit("/", 1)[0])).rsplit("/", 1)[-1]
        lines.append(f"Apparaat op {adapter}: {_value(device, 'Name', 'naam onbekend')}")
        for key in ("Connected", "ServicesResolved"):
            value = _value(device, key)
            label = "onbekend" if value is None else "yes" if value else "no"
            lines.append(f"  {key}: {label}")
        rssi = _value(device, "RSSI")
        if rssi is not None:
            lines.append(f"  Laatst waargenomen RSSI: {rssi} dBm")
    if not found:
        lines.append("Geen BlueZ-device voor dit adres gevonden; verbindingstatus onbekend.")
    lines.append("Alleen status opgevraagd. Er is niet gescand, verbonden of losgekoppeld.")
    return lines


async def get_status(address):
    from dbus_fast import BusType, Message, MessageType
    from dbus_fast.aio import MessageBus

    bus = await asyncio.wait_for(MessageBus(bus_type=BusType.SYSTEM).connect(), 8)
    try:
        reply = await asyncio.wait_for(bus.call(Message(
            destination="org.bluez", path="/",
            interface="org.freedesktop.DBus.ObjectManager", member="GetManagedObjects",
        )), 8)
        if reply.message_type == MessageType.ERROR:
            raise RuntimeError(f"BlueZ-status niet beschikbaar: {reply.error_name}: {reply.body}")
        return status_lines(reply.body[0], address)
    finally:
        bus.disconnect()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--address", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}", args.address):
        parser.error("Vul een Bluetooth-adres in, bijvoorbeeld 10:23:81:45:37:95")
    try:
        lines = asyncio.run(get_status(args.address))
    except ModuleNotFoundError:
        print("Gebruik /config/solis-ble-venv/bin/python; dbus-fast uit Bleak is nodig.", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"Statuscontrole mislukt: {type(error).__name__}: {error}", file=sys.stderr)
        print("Dit geeft geen uitsluitsel over de verbinding met de omvormer.", file=sys.stderr)
        return 1
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
