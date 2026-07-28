"""Config flow for Autarco Local."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.helpers import selector

from .const import (
    CONF_DEVICE_ID,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
    DEFAULT_DEVICE_ID,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MAX_TIMEOUT,
    MIN_SCAN_INTERVAL,
    MIN_TIMEOUT,
)
from .modbus_client import (
    AutarcoConnectionError,
    AutarcoConnectionSettings,
    AutarcoModbusClient,
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
    }


async def _validate_input(hass, data: dict[str, Any]) -> None:
    """Validate user input with a read-only Modbus request."""
    settings = AutarcoConnectionSettings(
        host=data[CONF_HOST],
        port=data[CONF_PORT],
        device_id=data[CONF_DEVICE_ID],
        timeout=data[CONF_TIMEOUT],
    )
    await hass.async_add_executor_job(AutarcoModbusClient(settings).validate)


def _get_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Return the config-flow schema."""
    defaults = defaults or {}

    return vol.Schema(
        {
            vol.Required(
                CONF_NAME,
                default=defaults.get(CONF_NAME, DEFAULT_NAME),
            ): selector.TextSelector(),
            vol.Required(
                CONF_HOST,
                default=defaults.get(CONF_HOST, ""),
            ): selector.TextSelector(
                selector.TextSelectorConfig(type="text")
            ),
            vol.Required(
                CONF_PORT,
                default=defaults.get(CONF_PORT, DEFAULT_PORT),
            ): selector.NumberSelector(
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
                default=defaults.get(
                    CONF_SCAN_INTERVAL,
                    DEFAULT_SCAN_INTERVAL,
                ),
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
        }
    )


class AutarcoLocalConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle an Autarco Local config flow."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            data = _normalize_input(user_input)

            await self.async_set_unique_id(
                f"{data[CONF_HOST]}:{data[CONF_PORT]}"
            )
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
                _LOGGER.exception(
                    "Onverwachte fout tijdens de Autarco-configuratie"
                )
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=data[CONF_NAME],
                    data=data,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_get_schema(user_input),
            errors=errors,
        )

    async def async_step_reconfigure(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Allow an existing connection to be changed."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            data = _normalize_input(user_input)

            try:
                await _validate_input(self.hass, data)
            except AutarcoConnectionError as err:
                _LOGGER.warning(
                    "Kan Autarco tijdens herconfiguratie niet bereiken: %s",
                    err,
                )
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception(
                    "Onverwachte fout tijdens Autarco-herconfiguratie"
                )
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
