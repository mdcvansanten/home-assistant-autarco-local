"""Config and options flows for Autarco Local."""

from __future__ import annotations

import logging
import re
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_BATTERY_SOC_ENTITY,
    CONF_BLE_ADDRESS,
    CONF_TRANSPORT,
    CONF_RUNTIME_VALIDATED,
    TRANSPORT_TCP,
    TRANSPORT_BLE,
    CONF_DEVICE_ID,
    CONF_RETRIES,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
    DEFAULT_DEVICE_ID,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_RETRIES,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    MAX_RETRIES,
    MAX_SCAN_INTERVAL,
    MAX_TIMEOUT,
    MIN_RETRIES,
    MIN_SCAN_INTERVAL,
    MIN_TIMEOUT,
)
from .modbus_client import (
    AutarcoConnectionError,
    AutarcoConnectionSettings,
    AutarcoModbusClient,
)
from .settings_security import (
    CONF_SETTINGS_PIN_HASH,
    CONF_SETTINGS_PIN_SALT,
    create_pin_credentials,
    pin_is_configured,
    validate_pin_format,
)

_LOGGER = logging.getLogger(__name__)

NEW_PIN_FIELD = "settings_new_pin"
CLEAR_PIN_FIELD = "settings_clear_pin"
PIN_STATUS_FIELD = "settings_pin_status"


def _normalize_input(user_input: dict[str, Any]) -> dict[str, Any]:
    """Normalize selector values before storing or validating them."""
    return {
        CONF_TRANSPORT: str(user_input.get(CONF_TRANSPORT, TRANSPORT_TCP)),
        CONF_BLE_ADDRESS: str(user_input.get(CONF_BLE_ADDRESS, "")).strip().upper(),
        CONF_NAME: str(user_input[CONF_NAME]).strip() or DEFAULT_NAME,
        CONF_HOST: str(user_input.get(CONF_HOST, "")).strip(),
        CONF_PORT: int(user_input[CONF_PORT]),
        CONF_DEVICE_ID: int(user_input[CONF_DEVICE_ID]),
        CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL]),
        CONF_TIMEOUT: int(user_input[CONF_TIMEOUT]),
        CONF_RETRIES: int(user_input.get(CONF_RETRIES, DEFAULT_RETRIES)),
    }


def _connection_id(data: dict[str, Any]) -> str:
    if data.get(CONF_TRANSPORT) == TRANSPORT_BLE:
        return f"ble:{data[CONF_BLE_ADDRESS]}"
    return f"{data[CONF_HOST]}:{data[CONF_PORT]}"


async def _validate_input(hass, data: dict[str, Any], entry=None) -> None:
    """Validate user input with a read-only Modbus request."""
    is_ble = data.get(CONF_TRANSPORT) == TRANSPORT_BLE
    if is_ble and not re.fullmatch(r"(?:[0-9A-F]{2}:){5}[0-9A-F]{2}", data[CONF_BLE_ADDRESS]):
        raise AutarcoConnectionError("Vul een geldig Bluetooth-adres in")
    if not is_ble and not data[CONF_HOST]:
        raise AutarcoConnectionError("Vul het IP-adres van de TCP-logger in")
    settings = AutarcoConnectionSettings(
        host=data[CONF_BLE_ADDRESS] if is_ble else data[CONF_HOST],
        port=data[CONF_PORT],
        device_id=data[CONF_DEVICE_ID],
        timeout=data[CONF_TIMEOUT],
        retries=data[CONF_RETRIES],
    )
    if is_ble:
        from .ble_client import AutarcoBleClient
        # Reconfigure a loaded BLE entry using its existing connection. A second
        # validation session could compete with the permanent session.
        if entry and getattr(entry, "runtime_data", None):
            existing = entry.runtime_data.client
            if isinstance(existing, AutarcoBleClient) and existing._settings.host == settings.host:
                await hass.async_add_executor_job(existing.validate)
                return
        client = AutarcoBleClient(hass, settings)
    else:
        client = AutarcoModbusClient(settings)
    await hass.async_add_executor_job(client.validate)


def _get_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Return the config-flow schema."""
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)): selector.TextSelector(),
            vol.Required(CONF_TRANSPORT, default=defaults.get(CONF_TRANSPORT, TRANSPORT_TCP)): selector.SelectSelector(
                selector.SelectSelectorConfig(options=[
                    {"value": TRANSPORT_TCP, "label": "Modbus TCP"},
                    {"value": TRANSPORT_BLE, "label": "Bluetooth LE (beta)"},
                ])
            ),
            vol.Optional(CONF_BLE_ADDRESS, default=defaults.get(CONF_BLE_ADDRESS, "")): selector.TextSelector(),
            vol.Optional(CONF_HOST, default=defaults.get(CONF_HOST, "")): selector.TextSelector(
                selector.TextSelectorConfig(type="text")
            ),
            vol.Required(CONF_PORT, default=defaults.get(CONF_PORT, DEFAULT_PORT)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=65535, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_DEVICE_ID,
                default=defaults.get(CONF_DEVICE_ID, DEFAULT_DEVICE_ID),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=247, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=defaults.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=MIN_SCAN_INTERVAL,
                    max=MAX_SCAN_INTERVAL,
                    mode=selector.NumberSelectorMode.BOX,
                    unit_of_measurement="s",
                )
            ),
            vol.Required(CONF_TIMEOUT, default=defaults.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=MIN_TIMEOUT,
                    max=MAX_TIMEOUT,
                    mode=selector.NumberSelectorMode.BOX,
                    unit_of_measurement="s",
                )
            ),
            vol.Required(CONF_RETRIES, default=defaults.get(CONF_RETRIES, DEFAULT_RETRIES)): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=MIN_RETRIES,
                    max=MAX_RETRIES,
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
        }
    )


class AutarcoLocalConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle an Autarco Local config flow."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Create the security and safety-source options flow."""
        return AutarcoLocalOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            data = _normalize_input(user_input)
            await self.async_set_unique_id(_connection_id(data))
            self._abort_if_unique_id_configured()
            try:
                await _validate_input(self.hass, data)
            except AutarcoConnectionError as err:
                _LOGGER.warning(
                    "Kan Autarco op %s:%s niet bereiken: %s",
                    data[CONF_HOST],
                    data[CONF_PORT],
                    err,
                )
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Onverwachte fout tijdens de Autarco-configuratie")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=data[CONF_NAME], data=data)
        return self.async_show_form(
            step_id="user",
            data_schema=_get_schema(user_input),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Allow an existing connection to be changed."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            data = _normalize_input(user_input)
            try:
                await _validate_input(self.hass, data, entry)
            except AutarcoConnectionError as err:
                _LOGGER.warning("Kan Autarco tijdens herconfiguratie niet bereiken: %s", err)
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Onverwachte fout tijdens Autarco-herconfiguratie")
                errors["base"] = "unknown"
            else:
                options = dict(entry.options)
                if _connection_id(dict(entry.data)) != _connection_id(data):
                    options[CONF_RUNTIME_VALIDATED] = False
                return self.async_update_reload_and_abort(
                    entry,
                    unique_id=_connection_id(data),
                    data=data,
                    options=options,
                )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_get_schema(user_input if user_input is not None else dict(entry.data)),
            errors=errors,
        )


class AutarcoLocalOptionsFlow(OptionsFlow):
    """Manage Settings security and the trusted battery-SOC source.

    Inverter settings live in the Autarco Local dashboard. The native Options
    flow is reserved for local integration policy: PIN security and selection of
    a Home Assistant battery-SOC entity that may be trusted by safety checks.
    """

    @staticmethod
    def _readonly_text() -> selector.TextSelector:
        return selector.TextSelector(selector.TextSelectorConfig(read_only=True))

    @staticmethod
    def _password_text() -> selector.TextSelector:
        return selector.TextSelector(selector.TextSelectorConfig(type="password"))

    @staticmethod
    def _battery_soc_selector() -> selector.EntitySelector:
        return selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor")
        )

    def _security_schema(self) -> vol.Schema:
        status = (
            "PIN ingesteld — ontgrendelen kan vanuit Autarco Local → Instellingen"
            if pin_is_configured(self.config_entry)
            else "Nog geen PIN ingesteld — alle writes blijven geblokkeerd"
        )
        fields: dict[Any, Any] = {
            vol.Optional(PIN_STATUS_FIELD, default=status): self._readonly_text(),
            vol.Optional(NEW_PIN_FIELD, default=""): self._password_text(),
            vol.Optional(CLEAR_PIN_FIELD, default=False): selector.BooleanSelector(),
            vol.Optional(CONF_RUNTIME_VALIDATED, default=self.config_entry.options.get(CONF_RUNTIME_VALIDATED, False)): selector.BooleanSelector(),
        }
        current_soc_entity = self.config_entry.options.get(CONF_BATTERY_SOC_ENTITY)
        if current_soc_entity:
            fields[
                vol.Optional(CONF_BATTERY_SOC_ENTITY, default=current_soc_entity)
            ] = self._battery_soc_selector()
        else:
            fields[vol.Optional(CONF_BATTERY_SOC_ENTITY)] = self._battery_soc_selector()
        return vol.Schema(fields)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage PIN and trusted battery-SOC source; never write inverter settings here."""
        errors: dict[str, str] = {}

        if user_input is not None:
            options = dict(self.config_entry.options)
            new_pin = str(user_input.get(NEW_PIN_FIELD, "")).strip()
            clear_pin = bool(user_input.get(CLEAR_PIN_FIELD, False))
            options[CONF_RUNTIME_VALIDATED] = bool(user_input.get(CONF_RUNTIME_VALIDATED, False))
            battery_soc_entity = str(
                user_input.get(CONF_BATTERY_SOC_ENTITY, "") or ""
            ).strip()

            if new_pin and clear_pin:
                errors["base"] = "pin_conflict"
            elif new_pin:
                try:
                    normalized_pin = validate_pin_format(new_pin)
                except ValueError:
                    errors["base"] = "invalid_pin"
                else:
                    salt, digest = create_pin_credentials(normalized_pin)
                    options[CONF_SETTINGS_PIN_SALT] = salt
                    options[CONF_SETTINGS_PIN_HASH] = digest
            elif clear_pin:
                options.pop(CONF_SETTINGS_PIN_SALT, None)
                options.pop(CONF_SETTINGS_PIN_HASH, None)

            if battery_soc_entity:
                options[CONF_BATTERY_SOC_ENTITY] = battery_soc_entity
            else:
                options.pop(CONF_BATTERY_SOC_ENTITY, None)

            if not errors:
                return self.async_create_entry(data=options)

        return self.async_show_form(
            step_id="init",
            data_schema=self._security_schema(),
            errors=errors,
        )
