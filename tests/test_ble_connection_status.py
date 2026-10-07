"""BlueZ status checks must be passive and preserve unknown states."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from dbus_fast import MessageType, Variant

spec = importlib.util.spec_from_file_location(
    "ble_connection_status", Path(__file__).resolve().parents[1] / "tools/ble_connection_status.py"
)
status = importlib.util.module_from_spec(spec)
spec.loader.exec_module(status)
ADDRESS = "10:23:81:45:37:95"


@pytest.mark.asyncio
async def test_status_reads_bluez_once_without_connect_or_discovery(monkeypatch):
    objects = {
        "/org/bluez/hci0": {"org.bluez.Adapter1": {"Powered": Variant("b", True)}},
        "/org/bluez/hci0/dev_target": {"org.bluez.Device1": {
            "Address": Variant("s", ADDRESS), "Connected": Variant("b", True),
            "ServicesResolved": Variant("b", True), "Name": Variant("s", "INV_test"),
        }},
        "/org/bluez/hci0/dev_other": {"org.bluez.Device1": {
            "Address": Variant("s", "AA:BB:CC:DD:EE:FF"), "Name": Variant("s", "Other device"),
        }},
    }
    bus = MagicMock()
    bus.connect = AsyncMock(return_value=bus)
    bus.call = AsyncMock(return_value=SimpleNamespace(message_type=MessageType.METHOD_RETURN, body=[objects]))
    monkeypatch.setattr("dbus_fast.aio.MessageBus", MagicMock(return_value=bus))
    lines = await status.get_status(ADDRESS)
    assert "  Connected: yes" in lines and "Other device" not in "\n".join(lines)
    message = bus.call.call_args.args[0]
    assert message.destination == "org.bluez"
    assert message.path == "/" and message.member == "GetManagedObjects"
    bus.call.assert_awaited_once()
    bus.disconnect.assert_called_once()


def test_missing_device_remains_unknown():
    lines = status.status_lines({}, ADDRESS)
    assert "verbindingstatus onbekend" in "\n".join(lines)
    assert "Connected: no" not in "\n".join(lines)


@pytest.mark.asyncio
async def test_bluez_error_still_releases_dbus_client(monkeypatch):
    bus = MagicMock()
    bus.connect = AsyncMock(return_value=bus)
    bus.call = AsyncMock(return_value=SimpleNamespace(
        message_type=MessageType.ERROR, error_name="org.freedesktop.DBus.Error.AccessDenied", body=[]
    ))
    monkeypatch.setattr("dbus_fast.aio.MessageBus", MagicMock(return_value=bus))
    with pytest.raises(RuntimeError, match="AccessDenied"):
        await status.get_status(ADDRESS)
    bus.disconnect.assert_called_once()
