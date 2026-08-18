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
    OFF_GRID_MINIMUM_SOC_PILOT_FROM,
    OFF_GRID_MINIMUM_SOC_PILOT_TO,
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
from .settings_security import (
    CONF_SETTINGS_PIN_HASH,
    CONF_SETTINGS_PIN_SALT,
    create_pin_credentials,
    pin_is_configured,
    validate_pin_format,
    verify_pin,
)
from .settings_write import async_write_off_grid_minimum_soc

_LOGGER = logging.getLogger(__name__)

SECURITY_SECTION = "settings_security"
NEW_PIN_FIELD = "settings_new_pin"
CLEAR_PIN_FIELD = "settings_clear_pin"
PIN_STATUS_FIELD = "settings_pin_status"
EXPERT_PIN_FIELD = "expert_write_pin"


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
        """Create the native Autarco Local Settings Center fallback flow."""
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
            data_schema=_get_schema(user_input if user_input is not None else dict(entry.data)),
            errors=errors,
        )


class AutarcoLocalOptionsFlow(OptionsFlow):
    """Provide the native Settings Center plus a PIN-protected write fallback."""

    def _coordinator(self):
        return getattr(self.config_entry, "runtime_data", None)

    def _settings_data(self) -> dict[int, int]:
        coordinator = self._coordinator()
        return getattr(coordinator, "settings_data", {}) or {}

    def _set_write_diagnostic(self, message: str) -> None:
        coordinator = self._coordinator()
        if coordinator is not None:
            coordinator.settings_last_write_diagnostic = message
        _LOGGER.warning("Autarco write-diagnose: %s", message)

    def _write_status_text(self) -> str:
        coordinator = self._coordinator()
        diagnostic = getattr(coordinator, "settings_last_write_diagnostic", None)
        security = "PIN ingesteld" if pin_is_configured(self.config_entry) else "PIN nog niet ingesteld"
        base = f"PILOT — alleen Off-grid minimum SOC 10% -> 20% is schrijfbaar; {security}"
        if not diagnostic:
            return f"{base}. Nog geen write-diagnose beschikbaar."
        return f"{base}. Laatste poging: {diagnostic}"

    @staticmethod
    def _readonly_text() -> selector.TextSelector:
        return selector.TextSelector(selector.TextSelectorConfig(read_only=True))

    @staticmethod
    def _password_text() -> selector.TextSelector:
        return selector.TextSelector(selector.TextSelectorConfig(type="password"))

    @staticmethod
    def _off_grid_soc_number() -> selector.NumberSelector:
        return selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=10,
                max=100,
                step=1,
                mode=selector.NumberSelectorMode.BOX,
                unit_of_measurement="%",
            )
        )

    def _format_setting(self, description) -> str:
        value = description.value_fn(self._settings_data())
        if value is None:
            return "Unavailable"
        unit = description.native_unit_of_measurement
        return f"{value} {unit}" if unit else str(value)

    def _security_schema(self) -> vol.Schema:
        status = (
            "PIN ingesteld — writes kunnen na ontgrendeling worden uitgevoerd"
            if pin_is_configured(self.config_entry)
            else "Nog geen PIN ingesteld — writes blijven geblokkeerd"
        )
        return vol.Schema(
            {
                vol.Optional(PIN_STATUS_FIELD, default=status): self._readonly_text(),
                vol.Optional(NEW_PIN_FIELD, default=""): self._password_text(),
                vol.Optional(CLEAR_PIN_FIELD, default=False): selector.BooleanSelector(),
            }
        )

    def _schema_for_access_level(
        self,
        access_level: str,
        *,
        enable_off_grid_soc_pilot: bool = False,
    ) -> vol.Schema:
        fields: dict[Any, Any] = {}
        for description in SETTINGS:
            if description.access_level != access_level:
                continue

            if (
                enable_off_grid_soc_pilot
                and description.key == "setting_off_grid_overdischarge_soc"
            ):
                current = self._settings_data().get(OFF_GRID_MINIMUM_SOC_REGISTER)
                fields[
                    vol.Optional(
                        description.key,
                        default=(
                            int(current)
                            if current is not None
                            else OFF_GRID_MINIMUM_SOC_PILOT_FROM
                        ),
                    )
                ] = self._off_grid_soc_number()
                continue

            fields[
                vol.Optional(description.key, default=self._format_setting(description))
            ] = self._readonly_text()

        if access_level == ACCESS_EXPERT and enable_off_grid_soc_pilot:
            fields[vol.Optional(EXPERT_PIN_FIELD, default="")] = self._password_text()
        return vol.Schema(fields)

    def _installer_schema(self) -> vol.Schema:
        fields = dict(self._schema_for_access_level(ACCESS_INSTALLER).schema)
        for key in UNMAPPED_INSTALLER_SETTINGS:
            fields[vol.Optional(key, default="Not mapped yet — read-only")] = self._readonly_text()
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
                vol.Optional("safety_reserve_soc", default=pct(reserve_soc)): self._readonly_text(),
                vol.Optional("safety_minimum_soc", default=pct(minimum_soc)): self._readonly_text(),
                vol.Optional("safety_force_charge_soc", default=pct(force_charge_soc)): self._readonly_text(),
                vol.Optional("safety_off_grid_minimum_soc", default=pct(off_grid_minimum_soc)): self._readonly_text(),
                vol.Optional("safety_soc_relationship", default=reserve_relationship): self._readonly_text(),
                vol.Optional("safety_force_relationship", default=force_relationship): self._readonly_text(),
                vol.Optional(
                    "safety_off_grid_review",
                    default=(
                        f"Current {off_grid_minimum_soc}% — write pilot target 20%"
                        if off_grid_minimum_soc is not None
                        else "Unavailable"
                    ),
                ): self._readonly_text(),
                vol.Optional("safety_write_status", default=self._write_status_text()): self._readonly_text(),
            }
        )

    def _settings_center_schema(self) -> vol.Schema:
        return vol.Schema(
            {
                vol.Required(SECURITY_SECTION): section(
                    self._security_schema(),
                    {"collapsed": False},
                ),
                vol.Required("standard_settings"): section(
                    self._schema_for_access_level(ACCESS_STANDARD),
                    {"collapsed": False},
                ),
                vol.Required("expert_settings"): section(
                    self._schema_for_access_level(
                        ACCESS_EXPERT,
                        enable_off_grid_soc_pilot=True,
                    ),
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
        """Show settings and support the guarded PIN-protected 10-to-20 pilot."""
        errors: dict[str, str] = {}

        if user_input is not None:
            options = dict(self.config_entry.options)
            security_data = user_input.get(SECURITY_SECTION, {}) or {}
            new_pin = str(security_data.get(NEW_PIN_FIELD, "")).strip()
            clear_pin = bool(security_data.get(CLEAR_PIN_FIELD, False))
            security_changed = bool(new_pin or clear_pin)

            if new_pin and clear_pin:
                errors["base"] = "unknown"
                self._set_write_diagnostic(
                    "AFGEBROKEN — kies óf een nieuwe PIN óf PIN verwijderen, niet beide"
                )
            elif new_pin:
                try:
                    normalized_pin = validate_pin_format(new_pin)
                except ValueError as err:
                    errors["base"] = "unknown"
                    self._set_write_diagnostic(f"AFGEBROKEN — {err}")
                else:
                    salt, digest = create_pin_credentials(normalized_pin)
                    options[CONF_SETTINGS_PIN_SALT] = salt
                    options[CONF_SETTINGS_PIN_HASH] = digest
            elif clear_pin:
                options.pop(CONF_SETTINGS_PIN_SALT, None)
                options.pop(CONF_SETTINGS_PIN_HASH, None)

            coordinator = self._coordinator()
            current = self._settings_data().get(OFF_GRID_MINIMUM_SOC_REGISTER)
            expert_data = user_input.get("expert_settings", {}) or {}
            requested_raw = expert_data.get(
                "setting_off_grid_overdischarge_soc",
                current,
            )
            expert_pin = str(expert_data.get(EXPERT_PIN_FIELD, "")).strip()

            try:
                requested = int(requested_raw) if requested_raw is not None else None
            except (TypeError, ValueError):
                requested = None

            write_requested = (
                requested is not None
                and current is not None
                and int(requested) != int(current)
            )

            if not errors and write_requested:
                if security_changed:
                    self._set_write_diagnostic(
                        "AFGEBROKEN — sla een gewijzigde PIN eerst apart op en open Configureren daarna opnieuw"
                    )
                    errors["base"] = "unknown"
                elif not pin_is_configured(self.config_entry):
                    self._set_write_diagnostic(
                        "AFGEBROKEN — stel eerst bovenaan een instellingen-PIN in"
                    )
                    errors["base"] = "unknown"
                elif not expert_pin or not verify_pin(self.config_entry, expert_pin):
                    self._set_write_diagnostic(
                        "AFGEBROKEN — onjuiste of ontbrekende instellingen-PIN voor Expert-write"
                    )
                    errors["base"] = "unknown"
                elif current != OFF_GRID_MINIMUM_SOC_PILOT_FROM or requested != OFF_GRID_MINIMUM_SOC_PILOT_TO:
                    self._set_write_diagnostic(
                        f"GEWEIGERD — actueel={current}%, aangevraagd={requested}%; alleen 10% -> 20% is toegestaan"
                    )
                    errors["base"] = "unknown"
                elif coordinator is None:
                    self._set_write_diagnostic(
                        "AFGEBROKEN — Home Assistant coordinator ontbreekt"
                    )
                    errors["base"] = "unknown"
                else:
                    try:
                        await async_write_off_grid_minimum_soc(
                            self.hass,
                            coordinator,
                            requested,
                        )
                    except Exception as err:
                        _LOGGER.exception(
                            "Fout tijdens PIN-beveiligde native Off-grid SOC write"
                        )
                        self._set_write_diagnostic(
                            f"MISLUKT — {type(err).__name__}: {err}"
                        )
                        errors["base"] = "unknown"
                    else:
                        return self.async_create_entry(data=options)

            if not errors and not write_requested:
                return self.async_create_entry(data=options)

        return self.async_show_form(
            step_id="init",
            data_schema=self._settings_center_schema(),
            errors=errors,
            description_placeholders={
                "write_status": (
                    "PILOT: Off-grid minimum SOC 10% -> 20% via PIN-beveiligde dependency-aware transactie"
                ),
                "docs_url": AUTARCO_LH_MII_MANUAL_URL,
            },
        )
