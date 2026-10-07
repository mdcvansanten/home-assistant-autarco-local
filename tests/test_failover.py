"""BLE/TCP failover, non-blocking recovery and single-source regression tests."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from custom_components.autarco_local.config_flow import _connection_id, _normalize_input, _validate_input
from custom_components.autarco_local.coordinator import AutarcoLocalCoordinator
from custom_components.autarco_local.failover_client import AutarcoFailoverClient
from custom_components.autarco_local.modbus_client import (
    AutarcoConnectionError, AutarcoConnectionSettings, AutarcoReadResult, AutarcoSettingsReadResult,
)
from custom_components.autarco_local.runtime_quality import EMS_REGISTERS
from custom_components.autarco_local import _async_handle_set_off_grid_minimum_soc


def result(transport, value=0):
    return AutarcoReadResult(dict.fromkeys(EMS_REGISTERS, value) | {33093: 348},
                             20, 15, 5, 1, (), 0, None, transport)


@pytest.fixture
async def client():
    router = AutarcoFailoverClient(None, AutarcoConnectionSettings("AA:BB:CC:DD:EE:FF", 502, 1, 1),
                                  AutarcoConnectionSettings("192.0.2.1", 502, 1, 1))
    router.ble = MagicMock(paused=False)
    router.ble.session = SimpleNamespace(connected=True, ensure_connected=AsyncMock(),
                                        read=AsyncMock(return_value=[348]), disconnect=AsyncMock())
    router.ble.read_all.return_value = result("ble")
    router.ble.read_settings.return_value = AutarcoSettingsReadResult({43024: 80}, 10, (), "ble")
    router.ble.transport_health = {"ble_connected": True, "ble_paused": False}
    router.ble.set_paused.side_effect = lambda value: setattr(router.ble, "paused", value)
    router.tcp = MagicMock()
    router.tcp._client = SimpleNamespace(connected=True)
    router.tcp.read_all.return_value = result("tcp", 20)
    router.tcp.read_settings.return_value = AutarcoSettingsReadResult({43024: 70}, 10, (), "tcp")
    return router


@pytest.mark.asyncio
async def test_ble_is_primary_and_real_zero_stays_valid(client):
    reading = await asyncio.to_thread(client.read_all)
    assert reading.source_transport == "ble"
    assert all(reading.registers[key] == 0 for key in EMS_REGISTERS)
    client.tcp.read_all.assert_not_called()
    assert client.active_transport == "ble" and not client.transport_health["fallback_active"]


@pytest.mark.asyncio
async def test_ble_failure_uses_one_whole_tcp_snapshot_and_remains_on_tcp(client):
    client.ble.read_all.side_effect = AutarcoConnectionError("BLE disconnected")
    reading = await asyncio.to_thread(client.read_all)
    assert reading.source_transport == "tcp"
    assert all(reading.registers[key] == 20 for key in EMS_REGISTERS)
    assert client.fallback_count == 1 and client.transport_health["fallback_active"]
    assert client.transport_health["fallback_reason"] == "BLE disconnected"
    await asyncio.to_thread(client.read_all)
    assert client.ble.read_all.call_count == 1
    assert client.tcp.read_all.call_count == 2
    settings = await asyncio.to_thread(client.read_settings)
    assert settings.source_transport == "tcp" and settings.registers[43024] == 70


@pytest.mark.asyncio
async def test_incomplete_ble_snapshot_falls_back_instead_of_publishing_missing_load(client):
    client.ble.read_all.return_value = AutarcoReadResult({33093: 348}, 20, 15, 5, 1, (), 0, None, "ble")
    reading = await asyncio.to_thread(client.read_all)
    assert reading.source_transport == "tcp" and EMS_REGISTERS.issubset(reading.registers)


@pytest.mark.asyncio
async def test_recovery_connect_does_not_block_tcp_polls_and_requires_full_ble_poll(client):
    client.ble.read_all.side_effect = AutarcoConnectionError("offline")
    await asyncio.to_thread(client.read_all)
    client._next_probe_at = 0
    started, release = asyncio.Event(), asyncio.Event()
    async def connect():
        started.set()
        await release.wait()
    client.ble.session.ensure_connected.side_effect = connect
    probe = asyncio.create_task(client.async_probe_primary())
    await started.wait()
    assert client.transport_health["ble_recovery_running"]
    reading = await asyncio.wait_for(asyncio.to_thread(client.read_all), 1)
    assert reading.source_transport == "tcp"
    release.set()
    await probe
    # A good temperature response alone has not yet changed the telemetry source.
    assert client.active_transport == "tcp"
    client.ble.read_all.side_effect = None
    reading = await asyncio.to_thread(client.read_all)
    assert reading.source_transport == "ble" and client.recovery_count == 1
    client.tcp.close.assert_called_once()


@pytest.mark.asyncio
async def test_failed_recovery_runtime_keeps_tcp_live(client):
    client.ble.read_all.side_effect = AutarcoConnectionError("offline")
    await asyncio.to_thread(client.read_all)
    client._next_probe_at = 0
    await client.async_probe_primary()
    reading = await asyncio.to_thread(client.read_all)
    assert reading.source_transport == "tcp" and client.recovery_count == 0
    assert not client.primary_probe_due


@pytest.mark.asyncio
async def test_both_routes_fail_without_a_zero_snapshot(client):
    client.ble.read_all.side_effect = AutarcoConnectionError("BLE unavailable")
    client.tcp.read_all.side_effect = AutarcoConnectionError("TCP unavailable")
    with pytest.raises(AutarcoConnectionError, match="BLE unavailable.*TCP unavailable"):
        await asyncio.to_thread(client.read_all)


@pytest.mark.asyncio
async def test_phone_handoff_keeps_tcp_and_suppresses_recovery_until_resume(client):
    await asyncio.to_thread(client.set_paused, True)
    reading = await asyncio.to_thread(client.read_all)
    assert reading.source_transport == "tcp" and not client.primary_probe_due
    await client.async_probe_primary()
    client.ble.read_all.assert_not_called()
    client.ble.session.ensure_connected.assert_not_awaited()
    await asyncio.to_thread(client.set_paused, False)
    assert client.primary_probe_due


@pytest.mark.asyncio
async def test_late_probe_cannot_promote_ble_after_pause(client):
    client._active_transport = "tcp"
    started, release = asyncio.Event(), asyncio.Event()
    async def connect():
        started.set()
        await release.wait()
    client.ble.session.ensure_connected.side_effect = connect
    task = asyncio.create_task(client.async_probe_primary())
    await started.wait()
    await asyncio.to_thread(client.set_paused, True)
    release.set()
    await task
    assert not client._primary_ready
    client.ble.session.read.assert_not_awaited()
    client.ble.session.disconnect.assert_awaited()
    assert (await asyncio.to_thread(client.read_all)).source_transport == "tcp"


@pytest.mark.asyncio
async def test_hybrid_validation_accepts_tcp_only_and_rejects_both_unreachable(client):
    client.ble.validate.side_effect = AutarcoConnectionError("BLE unavailable")
    await asyncio.to_thread(client.validate)
    client.tcp.validate.assert_called_once()
    client.tcp.validate.side_effect = AutarcoConnectionError("TCP unavailable")
    with pytest.raises(AutarcoConnectionError, match="BLE unavailable.*TCP unavailable"):
        await asyncio.to_thread(client.validate)
    assert not client.write_supported
    with pytest.raises(AutarcoConnectionError, match="alleen-lezen"):
        client._write_single_holding_locked(43137, 20, "test")


def hybrid_data():
    return {"name": "Garage", "transport": "ble_tcp", "ble_address": "AA:BB:CC:DD:EE:FF",
            "host": "192.0.2.1", "port": 502, "device_id": 1, "scan_interval": 15,
            "timeout": 5, "retries": 0}


@pytest.mark.asyncio
async def test_hybrid_schema_requires_existing_tcp_endpoint_and_keeps_ble_identity():
    data = _normalize_input(hybrid_data())
    assert _connection_id(data) == "ble:AA:BB:CC:DD:EE:FF"
    with pytest.raises(AutarcoConnectionError, match="TCP-logger"):
        await _validate_input(None, {**data, "host": ""})


@pytest.mark.asyncio
async def test_coordinator_source_changes_refresh_settings_without_entity_replacement(tmp_path, client):
    hass = HomeAssistant(str(tmp_path))
    entry = SimpleNamespace(entry_id="same-entry", data=hybrid_data(), options={}, title="Garage",
                            async_on_unload=MagicMock())
    coordinator = AutarcoLocalCoordinator(hass, entry)
    coordinator.client = client
    coordinator._async_save_history = AsyncMock()
    coordinator.data = await coordinator._async_update_data()
    assert coordinator.transport == coordinator.settings_transport == "ble"
    client.ble.read_all.side_effect = AutarcoConnectionError("BLE unavailable")
    coordinator.data = await coordinator._async_update_data()
    assert coordinator.transport == coordinator.settings_transport == "tcp"
    assert coordinator.data_quality == "live" and coordinator.connection_available
    assert not coordinator.network_health["write_supported"]
    assert any(event["event"] == "transport_changed" for event in coordinator.connection_events)
    await coordinator.async_set_ble_paused(True)
    coordinator.data = await coordinator._async_update_data()
    assert coordinator.data_quality == "live" and coordinator.transport == "tcp"
    await coordinator.async_shutdown()


@pytest.mark.asyncio
async def test_read_only_service_never_invokes_writer_during_tcp_fallback(monkeypatch, client):
    entry = SimpleNamespace(entry_id="same-entry")
    coordinator = SimpleNamespace(client=client)
    monkeypatch.setattr("custom_components.autarco_local._loaded_entry_and_coordinator",
                        lambda *args: (entry, coordinator))
    writer = AsyncMock()
    monkeypatch.setattr("custom_components.autarco_local.async_write_off_grid_minimum_soc_v066_safe", writer)
    call = SimpleNamespace(context=SimpleNamespace(user_id="test-user"), data={"soc": 20})
    with pytest.raises(HomeAssistantError, match="alleen-lezen"):
        await _async_handle_set_off_grid_minimum_soc(None, call)
    writer.assert_not_awaited()


@pytest.mark.asyncio
async def test_reconfigure_existing_ble_to_hybrid_reuses_existing_radio_session(monkeypatch):
    from custom_components.autarco_local.ble_client import AutarcoBleClient
    primary = AutarcoBleClient(None, AutarcoConnectionSettings("AA:BB:CC:DD:EE:FF", 502, 1, 5))
    primary.validate = MagicMock()
    entry = SimpleNamespace(runtime_data=SimpleNamespace(client=primary))
    hass = SimpleNamespace(async_add_executor_job=AsyncMock(side_effect=asyncio.to_thread))
    monkeypatch.setattr(AutarcoFailoverClient, "__init__", MagicMock(side_effect=AssertionError("second session")))
    await _validate_input(hass, hybrid_data(), entry)
    primary.validate.assert_called_once()
    AutarcoFailoverClient.__init__.assert_not_called()
