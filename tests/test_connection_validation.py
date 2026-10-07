"""Real logger socket reuse and actionable BLE timeout regression tests."""

import asyncio
import struct
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.autarco_local.ble_client import (
    AutarcoBleClient, BleOperationTimeout, BleSession,
)
from custom_components.autarco_local.config_flow import _validate_input
from custom_components.autarco_local.modbus_client import (
    AutarcoConnectionError, AutarcoConnectionSettings, AutarcoModbusClient,
)
from tests.test_ble import fake_client, response
from tests.test_failover import hybrid_data


@pytest.mark.asyncio
async def test_completed_coroutine_timeout_keeps_its_reason():
    client = AutarcoBleClient(None, AutarcoConnectionSettings("test", 502, 1, 1))

    async def timed_out():
        raise BleOperationTimeout("Bluetooth-time-out bij wachten op antwoord: register 33093")

    with pytest.raises(AutarcoConnectionError, match="wachten op antwoord.*33093") as caught:
        await asyncio.to_thread(client._submit, timed_out())
    assert "60 s" not in str(caught.value)


@pytest.mark.asyncio
async def test_unfinished_future_exceeding_guard_is_cancelled(monkeypatch):
    client = AutarcoBleClient(None, AutarcoConnectionSettings("test", 502, 1, 1))
    client.session.phase = "notificaties aanmelden (FFE2)"

    async def pending():
        await asyncio.Event().wait()

    operation = pending()
    future = MagicMock()
    future.result.side_effect = TimeoutError()
    future.done.return_value = False
    future.cancel.side_effect = operation.close
    monkeypatch.setattr(asyncio, "run_coroutine_threadsafe", lambda *args: future)
    with pytest.raises(AutarcoConnectionError, match="60 s.*FFE2"):
        await asyncio.to_thread(client._submit, operation)
    future.cancel.assert_called_once()
    future.exception.assert_not_called()


@pytest.mark.asyncio
async def test_response_timeout_reports_rejected_notifications_and_radio():
    session = BleSession(None, "test", 1, 0.02)
    session.client = fake_client()
    session.last_rssi, session.adapter_source = -89, "hci0"
    session.client.write_gatt_char.side_effect = lambda *args, **kwargs: session.receive(response(unit=2))
    with pytest.raises(BleOperationTimeout, match="wachten op antwoord.*33093") as caught:
        await session.read(4, 33093, 1)
    reason = str(caught.value)
    assert "notificaties=1" in reason and "geldige frames=0" in reason
    assert "adapter=hci0" in reason and "RSSI=-89 dBm" in reason
    assert not session.connected and session.timeouts == 1


@pytest.mark.asyncio
async def test_write_timeout_is_distinct_from_waiting_for_response():
    session = BleSession(None, "test", 1, 0.02)
    session.client = fake_client()

    async def blocked_write(*args, **kwargs):
        await asyncio.Event().wait()

    session.client.write_gatt_char.side_effect = blocked_write
    with pytest.raises(BleOperationTimeout, match="versturen.*FFE1.*33093"):
        await session.read(4, 33093, 1)
    assert not session.connected


@pytest.mark.asyncio
async def test_subscribe_timeout_closes_once_and_preserves_phase(monkeypatch):
    session = BleSession(None, "test", 1, 1)
    candidate = fake_client()
    candidate.start_notify.side_effect = TimeoutError()
    monkeypatch.setattr("custom_components.autarco_local.ble_client.bluetooth.async_ble_device_from_address",
                        lambda *args, **kwargs: SimpleNamespace(name="INV_test"))
    monkeypatch.setattr("custom_components.autarco_local.ble_client.bluetooth.async_last_service_info",
                        lambda *args, **kwargs: None)
    monkeypatch.setattr("custom_components.autarco_local.ble_client.establish_connection",
                        AsyncMock(return_value=candidate))
    with pytest.raises(BleOperationTimeout, match="notificaties aanmelden.*FFE2"):
        await session.ensure_connected()
    candidate.disconnect.assert_awaited_once()
    assert not session.connected


@pytest.mark.asyncio
async def test_ble_validation_preserves_existing_connection():
    client = AutarcoBleClient(None, AutarcoConnectionSettings("test", 502, 1, 1))
    candidate = client.session.client = fake_client()
    candidate.write_gatt_char.side_effect = lambda *args, **kwargs: client.session.receive(response())
    await asyncio.to_thread(client.validate)
    assert client.session.connected
    candidate.disconnect.assert_not_awaited()
    await client.session.disconnect()


@pytest.mark.asyncio
@pytest.mark.parametrize("transport", ["ble_tcp", "tcp"])
async def test_reconfigure_reuses_real_existing_logger_socket(monkeypatch, transport):
    accepted = 0
    requests = []

    async def serve(reader, writer):
        nonlocal accepted
        accepted += 1
        try:
            while True:
                header = await reader.readexactly(7)
                transaction, protocol, length, unit = struct.unpack(">HHHB", header)
                request = await reader.readexactly(length - 1)
                function, address, count = struct.unpack(">BHH", request)
                assert protocol == 0 and function == 4
                requests.append((address, count))
                payload = bytes((4, count * 2)) + b"\x00\x01" * count
                writer.write(struct.pack(">HHHB", transaction, 0, len(payload) + 1, unit) + payload)
                await writer.drain()
        except asyncio.IncompleteReadError:
            pass
        finally:
            writer.close()
            await writer.wait_closed()

    server = await asyncio.start_server(serve, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    settings = AutarcoConnectionSettings("127.0.0.1", port, 1, 1)
    client = AutarcoModbusClient(settings)
    try:
        await asyncio.to_thread(client._ensure_connected_locked)
        initial_socket = client._client
        entry = SimpleNamespace(runtime_data=SimpleNamespace(client=client))
        hass = SimpleNamespace(async_add_executor_job=AsyncMock(side_effect=asyncio.to_thread))
        monkeypatch.setattr(AutarcoBleClient, "validate",
                            MagicMock(side_effect=AutarcoConnectionError("Bluetooth-test mislukt")))
        data = {**hybrid_data(), "host": settings.host, "port": port, "transport": transport}
        await _validate_input(hass, data, entry)
        await _validate_input(hass, data, entry)
        assert accepted == 1 and len(requests) == 2
        assert client._client is initial_socket and client._client.connected
    finally:
        await asyncio.to_thread(client.close)
        server.close()
        await server.wait_closed()
        await asyncio.sleep(0)


def test_temporary_tcp_validation_closes_its_socket():
    client = AutarcoModbusClient(AutarcoConnectionSettings("test", 502, 1, 1))
    socket = MagicMock()
    socket.connected = True
    socket.read_input_registers.return_value = SimpleNamespace(isError=lambda: False, registers=[1])
    client._new_client = MagicMock(return_value=socket)
    client.validate()
    socket.connect.assert_called_once()
    socket.close.assert_called_once()
    assert client._client is None


def test_failed_tcp_read_discards_existing_socket():
    client = AutarcoModbusClient(AutarcoConnectionSettings("192.0.2.1", 502, 1, 1))
    socket = client._client = MagicMock(connected=True)
    socket.read_input_registers.side_effect = TimeoutError("Geen antwoord")
    with pytest.raises(AutarcoConnectionError, match="192.0.2.1:502.*Device-ID 1.*Geen antwoord"):
        client.validate()
    socket.close.assert_called_once()
    assert client._client is None


@pytest.mark.asyncio
async def test_reconfigure_preserves_both_errors_with_existing_ble(monkeypatch):
    primary = AutarcoBleClient(None, AutarcoConnectionSettings("AA:BB:CC:DD:EE:FF", 502, 1, 5))
    primary.validate = MagicMock(side_effect=AutarcoConnectionError("FFE2 geen antwoord"))
    entry = SimpleNamespace(runtime_data=SimpleNamespace(client=primary))
    hass = SimpleNamespace(async_add_executor_job=AsyncMock(side_effect=asyncio.to_thread))
    monkeypatch.setattr(AutarcoModbusClient, "validate",
                        MagicMock(side_effect=AutarcoConnectionError("TCP geen antwoord")))
    with pytest.raises(AutarcoConnectionError, match="FFE2 geen antwoord.*TCP geen antwoord"):
        await _validate_input(hass, hybrid_data(), entry)
