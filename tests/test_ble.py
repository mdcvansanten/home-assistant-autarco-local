"""Regression tests for actual captured frames, recovery and quality gates."""

import asyncio
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from custom_components.autarco_local.ble_protocol import (
    ModbusReadException, ReadFrameStream, crc16, decode_read, read_request,
)
from custom_components.autarco_local.ble_client import AutarcoBleClient, BleSession
from custom_components.autarco_local.config_flow import _get_schema, _normalize_input, _validate_input
from custom_components.autarco_local.config_flow import AutarcoLocalConfigFlow
from custom_components.autarco_local.coordinator import AutarcoLocalCoordinator
from custom_components.autarco_local.modbus_client import (
    AutarcoConnectionError, AutarcoConnectionSettings, AutarcoReadResult, AutarcoSettingsReadResult,
)
from custom_components.autarco_local.runtime_quality import EMS_REGISTERS, runtime_quality
from custom_components.autarco_local.sensor import RegisterSensor, SENSORS, SettingSensor
from custom_components.autarco_local.settings import SETTINGS


def response(function=4, values=(348,), unit=1):
    body = bytes((unit, function, len(values) * 2)) + b"".join(v.to_bytes(2, "big") for v in values)
    return body + crc16(body)


def exception_frame(code=2, function=4):
    body = bytes((1, function | 0x80, code))
    return body + crc16(body)


def test_real_captured_frames():
    assert read_request(4, 33093, 1).hex(" ") == "fe 04 81 45 00 01 1c 2c"
    assert decode_read(bytes.fromhex("01 04 02 01 5b f9 5b"), 4, 1) == [347]
    assert decode_read(bytes.fromhex("01 04 02 01 5c b8 99"), 4, 1) == [348]


@pytest.mark.parametrize("split", range(1, 7))
def test_fragmented_real_response(split):
    stream = ReadFrameStream({1, 254})
    frame = response()
    assert stream.feed(frame[:split]) == []
    assert stream.feed(frame[split:]) == [frame]


def test_coalescing_corruption_and_false_incomplete_header():
    stream = ReadFrameStream({1, 254})
    damaged = bytearray(response()); damaged[-1] ^= 0x55
    first, second = response(), response(3, (20,))
    assert stream.feed(b"\x01\x04\xf0" + bytes(damaged) + first + second) == [first, second]
    assert stream.dropped_bytes == 10


def test_bad_crc_wrong_function_wrong_length_and_exception():
    with pytest.raises(ValueError):
        decode_read(response()[:-1] + b"\x00", 4, 1)
    with pytest.raises(ValueError):
        decode_read(response(3), 4, 1)
    with pytest.raises(ValueError):
        decode_read(response(values=(1, 2)), 4, 1)
    with pytest.raises(ModbusReadException) as caught:
        decode_read(exception_frame(2), 4, 1)
    assert caught.value.code == 2


@pytest.mark.parametrize("args", [(6, 43024, 1), (4, -1, 1), (4, 33093, 0), (3, 65535, 2), (4, 33093, 126)])
def test_request_rejects_writes_and_bad_ranges(args):
    with pytest.raises(ValueError):
        read_request(*args)


def test_stream_bounds_noise_and_rejects_wrong_unit():
    stream = ReadFrameStream({1, 254})
    assert stream.feed(response(unit=2)) == []
    stream.feed(b"\0" * 2000)
    assert len(stream.buffer) <= 512
    assert stream.feed(response()) == [response()]


def fake_client():
    client = SimpleNamespace(is_connected=True)
    client.services = MagicMock()
    client.services.get_characteristic.return_value = object()
    client.clear_cache = AsyncMock()
    client.start_notify = AsyncMock()
    client.write_gatt_char = AsyncMock()
    async def disconnect():
        client.is_connected = False
    client.disconnect = AsyncMock(side_effect=disconnect)
    return client


@pytest.mark.asyncio
async def test_session_reads_expected_unit_without_reconnecting():
    session = BleSession(None, "AA:BB:CC:DD:EE:FF", 1, 1)
    client = session.client = fake_client()
    async def write(_char, data, **kwargs):
        assert data[0] == 254
        assert data[1] == 4
        session.receive(response()[:3]); session.receive(response()[3:])
    client.write_gatt_char.side_effect = write
    assert await session.read(4, 33093, 1) == [348]
    assert await session.read(4, 33093, 1) == [348]
    assert client.disconnect.await_count == 0


@pytest.mark.asyncio
async def test_simultaneous_connect_requests_establish_only_one_client(monkeypatch):
    session = BleSession(None, "test", 1, 1)
    monkeypatch.setattr("custom_components.autarco_local.ble_client.bluetooth.async_ble_device_from_address", lambda *a, **k: SimpleNamespace(name="INV_test"))
    monkeypatch.setattr("custom_components.autarco_local.ble_client.bluetooth.async_last_service_info", lambda *a, **k: None)
    async def connect(*args, **kwargs):
        await asyncio.sleep(0.01)
        return fake_client()
    establish = AsyncMock(side_effect=connect)
    monkeypatch.setattr("custom_components.autarco_local.ble_client.establish_connection", establish)
    assert await asyncio.gather(session.ensure_connected(), session.ensure_connected()) == [True, False]
    establish.assert_awaited_once()
    await session.disconnect()


@pytest.mark.asyncio
async def test_unmatched_frames_do_not_complete_request():
    session = BleSession(None, "test", 1, 1)
    session.client = fake_client()
    async def write(*args, **kwargs):
        session.receive(response(3) + response(values=(1, 2)) + response())
    session.client.write_gatt_char.side_effect = write
    assert await session.read(4, 33093, 1) == [348]
    assert session.unmatched_frames == 2


@pytest.mark.asyncio
async def test_timeout_resets_link_and_old_notification_generation(monkeypatch):
    session = BleSession(None, "test", 1, 0.02)
    clients = [fake_client(), fake_client()]
    monkeypatch.setattr("custom_components.autarco_local.ble_client.bluetooth.async_ble_device_from_address", lambda *a, **k: SimpleNamespace(name="INV_test"))
    monkeypatch.setattr("custom_components.autarco_local.ble_client.bluetooth.async_last_service_info", lambda *a, **k: None)
    establish = AsyncMock(side_effect=clients)
    monkeypatch.setattr("custom_components.autarco_local.ble_client.establish_connection", establish)
    await session.ensure_connected()
    old_notification = clients[0].start_notify.call_args.args[1]
    with pytest.raises(TimeoutError):
        await session.read(4, 33093, 1)
    assert not session.connected and session.timeouts == 1
    await session.ensure_connected()
    new_notification = clients[1].start_notify.call_args.args[1]
    async def write(*args, **kwargs):
        old_notification(None, response(values=(999,)))
        new_notification(None, response(values=(348,)))
    clients[1].write_gatt_char.side_effect = write
    assert await session.read(4, 33093, 1) == [348]
    assert establish.await_count == 2


@pytest.mark.asyncio
async def test_parallel_requests_are_serialized():
    session = BleSession(None, "test", 1, 1)
    session.client = fake_client()
    in_flight = 0
    async def write(*args, **kwargs):
        nonlocal in_flight
        in_flight += 1
        assert in_flight == 1
        await asyncio.sleep(0.002)
        session.receive(response())
        in_flight -= 1
    session.client.write_gatt_char.side_effect = write
    assert await asyncio.gather(session.read(4, 33093, 1), session.read(4, 33093, 1)) == [[348], [348]]


@pytest.mark.asyncio
async def test_valid_exception_preserves_link_and_writes_are_blocked():
    session = BleSession(None, "test", 1, 1)
    session.client = fake_client()
    session.client.write_gatt_char.side_effect = lambda *a, **k: session.receive(exception_frame())
    with pytest.raises(ModbusReadException):
        await session.read(4, 33093, 1)
    assert session.connected
    facade = AutarcoBleClient(None, AutarcoConnectionSettings("test", 0, 1, 1))
    with pytest.raises(AutarcoConnectionError, match="alleen-lezen"):
        facade._write_single_holding_locked(43110, 4, "test")


@pytest.mark.parametrize("failed,age,expected", [(False, 0, "live"), (True, 0, "stale"), (False, 61, "stale"), (False, None, "unavailable")])
def test_quality_keeps_real_zero_and_marks_old_data(failed, age, expected):
    assert runtime_quality(dict.fromkeys(EMS_REGISTERS, 0), failed=failed, age=age, max_age=60) == expected
    assert runtime_quality({33093: 348}, failed=False, age=0, max_age=60) == "partial"


def config_data():
    return {"name": "Garage", "host": "127.0.0.1", "port": 502, "device_id": 1, "scan_interval": 15, "timeout": 5, "retries": 0}


def entry(options=None):
    return SimpleNamespace(entry_id="test", data=config_data(), options=options or {}, title="Garage", async_on_unload=MagicMock())


@pytest.mark.asyncio
async def test_new_config_schema_and_defaults():
    data = _normalize_input(config_data())
    assert data["transport"] == "tcp"
    assert _get_schema()(config_data())["transport"] == "tcp"
    assert _normalize_input({**config_data(), "transport": "ble", "ble_address": "aa:bb:cc:dd:ee:ff"})["ble_address"] == "AA:BB:CC:DD:EE:FF"
    with pytest.raises(AutarcoConnectionError):
        await _validate_input(None, {**data, "transport": "ble", "ble_address": "wrong"})


@pytest.mark.asyncio
async def test_monitoring_survives_settings_failure_and_stale_data_is_unavailable(tmp_path):
    hass = HomeAssistant(str(tmp_path))
    ent = entry()
    co = AutarcoLocalCoordinator(hass, ent)
    co._async_save_history = AsyncMock()
    co.client = MagicMock()
    registers = dict.fromkeys(EMS_REGISTERS, 0) | {33093: 348}
    co.client.read_all.return_value = AutarcoReadResult(registers, 10, 8, 2, 1, (), 0, None)
    co.client.read_settings.side_effect = AutarcoConnectionError("settings unavailable")
    co.data = await co._async_update_data()
    assert co.data_quality == "live"
    assert co.settings_last_error == "settings unavailable"
    load = RegisterSensor(co, ent, next(d for d in SENSORS if d.key == "house_load_power"))
    assert load.available and load.native_value == 0
    co.client.read_all.side_effect = AutarcoConnectionError("link failed")
    assert await co._async_update_data() == registers
    assert co.data_quality == "stale" and not load.available
    assert not co.ems_data_ready
    await co.async_shutdown()


@pytest.mark.asyncio
async def test_missing_runtime_dependency_never_becomes_zero_or_valid_ems(tmp_path):
    hass = HomeAssistant(str(tmp_path))
    ent = entry({"runtime_mapping_validated": True})
    co = AutarcoLocalCoordinator(hass, ent)
    co.last_success_at = dt_util.utcnow()
    co.data = dict.fromkeys(EMS_REGISTERS, 0)
    co.successful_polls = 5; co.runtime_read_span_ms = 500
    assert co.ems_data_ready
    del co.data[33150]
    assert co.data_quality == "partial" and not co.ems_data_ready
    battery = RegisterSensor(co, ent, next(d for d in SENSORS if d.key == "battery_power"))
    assert not battery.available and battery.native_value is None
    await co.async_shutdown()


@pytest.mark.asyncio
async def test_settings_age_and_poll_frequency_are_separate(tmp_path):
    hass = HomeAssistant(str(tmp_path))
    ent = entry(); co = AutarcoLocalCoordinator(hass, ent)
    co._async_save_history = AsyncMock(); co.client = MagicMock()
    co.client.read_all.return_value = AutarcoReadResult(dict.fromkeys(EMS_REGISTERS, 0) | {33093: 348}, 10, 8, 2, 1, (), 0, None)
    co.client.read_settings.return_value = AutarcoSettingsReadResult({43024: 80}, 10, ())
    co.data = await co._async_update_data()
    co.data = await co._async_update_data()
    assert co.client.read_settings.call_count == 1
    setting = SettingSensor(co, ent, next(d for d in SETTINGS if d.key == "setting_reserve_soc"))
    assert setting.available
    co.settings_last_success_at = dt_util.utcnow() - timedelta(seconds=121)
    assert not setting.available and co.settings_status == "stale"
    await co.async_shutdown()


@pytest.mark.asyncio
async def test_initial_config_validates_without_existing_entry(monkeypatch):
    flow = AutarcoLocalConfigFlow()
    flow.hass = MagicMock()
    flow.async_set_unique_id = AsyncMock()
    flow._abort_if_unique_id_configured = MagicMock()
    flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})
    validate = AsyncMock()
    monkeypatch.setattr("custom_components.autarco_local.config_flow._validate_input", validate)
    assert await flow.async_step_user(config_data()) == {"type": "create_entry"}
    validate.assert_awaited_once()
    assert len(validate.call_args.args) == 2


@pytest.mark.asyncio
async def test_reconfigure_preserves_entry_and_resets_validation(monkeypatch):
    ent = entry({"runtime_mapping_validated": True, "settings_pin_hash": "test-only"})
    flow = AutarcoLocalConfigFlow(); flow.hass = MagicMock()
    flow._get_reconfigure_entry = MagicMock(return_value=ent)
    flow.async_update_reload_and_abort = MagicMock(return_value={"type": "abort"})
    monkeypatch.setattr("custom_components.autarco_local.config_flow._validate_input", AsyncMock())
    assert await flow.async_step_reconfigure({**config_data(), "transport": "ble", "ble_address": "AA:BB:CC:DD:EE:FF"}) == {"type": "abort"}
    call = flow.async_update_reload_and_abort.call_args
    assert call.args[0] is ent
    assert not call.kwargs["options"]["runtime_mapping_validated"]
    assert call.kwargs["options"]["settings_pin_hash"] == "test-only"


@pytest.mark.asyncio
async def test_ble_illegal_register_fallback_keeps_other_registers(monkeypatch):
    facade = AutarcoBleClient(None, AutarcoConnectionSettings("test", 0, 1, 1))
    async def read(_function, start, count):
        if start <= 33134 < start + count:
            raise ModbusReadException(2)
        return [25] * count
    facade.session.read = read
    result, unsupported = await asyncio.to_thread(facade._read_blocks_locked, 4, [(33133, 3)])
    assert result == {33133: 25, 33135: 25}
    assert unsupported == ["33134-33134"]


def test_all_sensor_dependencies_have_narrow_ble_coverage():
    from custom_components.autarco_local.const import BLE_RUNTIME_BLOCKS
    from custom_components.autarco_local.runtime_quality import SENSOR_REGISTERS
    coverage = {r for start, count in BLE_RUNTIME_BLOCKS for r in range(start, start + count)}
    assert set(SENSOR_REGISTERS) == {desc.key for desc in SENSORS}
    assert all(set(registers).issubset(coverage) for registers in SENSOR_REGISTERS.values())
