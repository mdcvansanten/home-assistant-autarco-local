"""Config and options flows for Autarco Local."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import callback
from homeassistant.data_entry_flow import section
from homeassistant.helpers import selector

from .const import (
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
    OFF_GRID_MINIMUM_SOC_REGISTER,
)
from .settings import (
    ACCESS_EXPERT,
    ACCESS_INSTALLER,
    ACCESS_STANDARD,
    AUTARCO_LH_MII_MANUAL_URL,
    SETTINGS,
    UNMAPPED_INSTALLER_SETTINGS,
    SettingValidationError,
    validate_soc_relationship,
)

_LOGGER = logging.getLogger(__name__)


def _normalize_input(user_input: dict[str, Any]) -> dict[str, Any]:
    """Normalize selector values before storing or validating them."""
    return {
        CONF_NAME: str(user_input[CONF_NAME]).strip() or DEFAULT_NAME,
        CONF_HOST: str(user_input[CONF_HOST]).strip(),
        CONF_PORT: int(user_input[CONF_PORT]),
        CONF_DEVICE_ID: int(user_input[CONF_DEVICE_ID]),
        CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL]),
        CONF_TIMEOUT: int(user_input[CONF_TIMEOUT]),
        CONF_RETRIES: int(user_input.get(CONF_RETRIES, DEFAULT_RETRIES)),
    }


async def _validate_input(hass, data: dict[str, Any]) -> None:
    """Validate user input with a read-only Modbus request."""
    settings = AutarcoConnectionSettings(
        host=data[CONF_HOST],
        port=data[CONF_PORT],
        device_id=data[CONF_DEVICE_ID],
        timeout=data[CONF_TIMEOUT],
        retries=data[CONF_RETRIES],
    )
    await hass.async_add_executor_job(AutarcoModbusClient(settings).validate)


def _get_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Return the config-flow schema."""
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)): selector.TextSelector(),
            vol.Required(CONF_HOST, default=defaults.get(CONF_HOST, "")): selector.TextSelector(
                selector.TextSelectorConfig(type="text")
            ),
            vol.Required(CONF_PORT, default=defaults.get(CONF_PORT, DEFAULT_PORT)): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1,
                    max=65535,
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Required(
                CONF_DEVICE_ID,
                default=defaults.get(CONF_DEVICE_ID, DEFAULT_DEVICE_ID),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1,
                    max=247,
                    mode=selector.NumberSelectorMode.BOX,
                )
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
            vol.Required(
                CONF_TIMEOUT,
                default=defaults.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=MIN_TIMEOUT,
                    max=MAX_TIMEOUT,
                    mode=selector.NumberSelectorMode.BOX,
                    unit_of_measurement="s",
                )
            ),
            vol.Required(
                CONF_RETRIES,
                default=defaults.get(CONF_RETRIES, DEFAULT_RETRIES),
            ): selector.NumberSelector(
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
        """Create the native read-only Settings Center fallback flow."""
        return AutarcoLocalOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            data = _normalize_input(user_input)
            await self.async_set_unique_id(f"{data[CONF_HOST]}:{data[CONF_PORT]}")
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
                await _validate_input(self.hass, data)
            except AutarcoConnectionError as err:
                _LOGGER.warning("Kan Autarco tijdens herconfiguratie niet bereiken: %s", err)
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Onverwachte fout tijdens Autarco-herconfiguratie")
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    unique_id=f"{data[CONF_HOST]}:{data[CONF_PORT]}",
                    data=data,
                )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_get_schema(
                user_input if user_input is not None else dict(entry.data)
            ),
            errors=errors,
        )


class AutarcoLocalOptionsFlow(OptionsFlow):
    """Provide a native read-only fallback for the custom Settings Center."""

    def _coordinator(self):
        return getattr(self.config_entry, "runtime_data", None)

    def _settings_data(self) -> dict[int, int]:
        coordinator = self._coordinator()
        return getattr(coordinator, "settings_data", {}) or {}

    @staticmethod
    def _readonly_text() -> selector.TextSelector:
        return selector.TextSelector(selector.TextSelectorConfig(read_only=True))

    def _format_setting(self, description) -> str:
        value = description.value_fn(self._settings_data())
        if value is None:
            return "Unavailable"
        unit = description.native_unit_of_measurement
        return f"{value} {unit}" if unit else str(value)

    def _schema_for_access_level(self, access_level: str) -> vol.Schema:
        fields: dict[Any, Any] = {}
        for description in SETTINGS:
            if description.access_level != access_level:
                continue
            fields[
                vol.Optional(description.key, default=self._format_setting(description))
            ] = self._readonly_text()
        return vol.Schema(fields)

    def _installer_schema(self) -> vol.Schema:
        fields = dict(self._schema_for_access_level(ACCESS_INSTALLER).schema)
        for key in UNMAPPED_INSTALLER_SETTINGS:
            fields[vol.Optional(key, default="Not mapped yet — read-only")] = (
                self._readonly_text()
            )
        return vol.Schema(fields)

    def _safety_schema(self) -> vol.Schema:
        data = self._settings_data()
        reserve_soc = data.get(43024)
        minimum_soc = data.get(43011)
        force_charge_soc = data.get(43018)
        off_grid_minimum_soc = data.get(OFF_GRID_MINIMUM_SOC_REGISTER)

        reserve_relationship = "Unavailable"
        if reserve_soc is not None and minimum_soc is not None:
            try:
                validate_soc_relationship(reserve_soc, minimum_soc)
            except SettingValidationError:
                reserve_relationship = "INVALID — Reserve SOC is below Minimum battery SOC"
            else:
                reserve_relationship = f"OK — {reserve_soc}% >= {minimum_soc}%"

        force_relationship = "Unavailable"
        if force_charge_soc is not None and minimum_soc is not None:
            force_relationship = (
                f"{force_charge_soc}% < {minimum_soc}%"
                if force_charge_soc < minimum_soc
                else f"CHECK — {force_charge_soc}% >= {minimum_soc}%"
            )

        def pct(value: int | None) -> str:
            return f"{value}%" if value is not None else "Unavailable"

        return vol.Schema(
            {
                vol.Optional(
                    "safety_reserve_soc", default=pct(reserve_soc)
                ): self._readonly_text(),
                vol.Optional(
                    "safety_minimum_soc", default=pct(minimum_soc)
                ): self._readonly_text(),
                vol.Optional(
                    "safety_force_charge_soc", default=pct(force_charge_soc)
                ): self._readonly_text(),
                vol.Optional(
                    "safety_off_grid_minimum_soc", default=pct(off_grid_minimum_soc)
                ): self._readonly_text(),
                vol.Optional(
                    "safety_soc_relationship", default=reserve_relationship
                ): self._readonly_text(),
                vol.Optional(
                    "safety_force_relationship", default=force_relationship
                ): self._readonly_text(),
                vol.Optional(
                    "safety_off_grid_review",
                    default=(
                        "Gebruik het Autarco Local-zijbalkpaneel voor de begeleide "
                        "Off-grid minimum SOC 10% → 20% hardwarepilot."
                    ),
                ): self._readonly_text(),
                vol.Optional(
                    "safety_write_status",
                    default=(
                        "Deze native Configure/Options-flow is bewust read-only. "
                        "Expert-writes lopen uitsluitend via de begeleide preflight."
                    ),
                ): self._readonly_text(),
            }
        )

    def _settings_center_schema(self) -> vol.Schema:
        return vol.Schema(
            {
                vol.Required("standard_settings"): section(
                    self._schema_for_access_level(ACCESS_STANDARD),
                    {"collapsed": False},
                ),
                vol.Required("expert_settings"): section(
                    self._schema_for_access_level(ACCESS_EXPERT),
                    {"collapsed": False},
                ),
                vol.Required("installer_settings"): section(
                    self._installer_schema(),
                    {"collapsed": True},
                ),
                vol.Required("safety_rules"): section(
                    self._safety_schema(),
                    {"collapsed": False},
                ),
            }
        )

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show a read-only native fallback; physical writes live in the panel."""
        if user_input is not None:
            return self.async_create_entry(data={})

        return self.async_show_form(
            step_id="init",
            data_schema=self._settings_center_schema(),
            description_placeholders={
                "write_status": (
                    "READ-ONLY: gebruik het Autarco Local-zijbalkpaneel voor "
                    "begeleide Expert-writes"
                ),
                "docs_url": AUTARCO_LH_MII_MANUAL_URL,
            },
        )
