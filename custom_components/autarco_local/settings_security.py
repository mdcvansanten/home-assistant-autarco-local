"""Settings unlock security for Autarco Local."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from typing import Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

CONF_SETTINGS_PIN_HASH: Final = "settings_pin_hash"
CONF_SETTINGS_PIN_SALT: Final = "settings_pin_salt"
DATA_SETTINGS_UNLOCKS: Final = f"{DOMAIN}_settings_unlocks"
PIN_MIN_LENGTH: Final = 4
PIN_MAX_LENGTH: Final = 8
PIN_ITERATIONS: Final = 200_000
SETTINGS_UNLOCK_SECONDS: Final = 10 * 60


def validate_pin_format(pin: str) -> str:
    """Validate and normalize a settings PIN."""
    normalized = str(pin).strip()
    if not normalized.isdigit():
        raise ValueError("De instellingen-PIN mag alleen cijfers bevatten.")
    if not PIN_MIN_LENGTH <= len(normalized) <= PIN_MAX_LENGTH:
        raise ValueError(
            f"De instellingen-PIN moet {PIN_MIN_LENGTH} tot {PIN_MAX_LENGTH} cijfers lang zijn."
        )
    return normalized


def create_pin_credentials(pin: str) -> tuple[str, str]:
    """Create a salted PBKDF2 hash for a settings PIN."""
    normalized = validate_pin_format(pin)
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        normalized.encode("utf-8"),
        bytes.fromhex(salt),
        PIN_ITERATIONS,
    ).hex()
    return salt, digest


def pin_is_configured(entry: ConfigEntry) -> bool:
    """Return whether the config entry has a complete PIN credential pair."""
    return bool(
        entry.options.get(CONF_SETTINGS_PIN_SALT)
        and entry.options.get(CONF_SETTINGS_PIN_HASH)
    )


def verify_pin(entry: ConfigEntry, pin: str) -> bool:
    """Verify a PIN against the stored salted hash."""
    salt = entry.options.get(CONF_SETTINGS_PIN_SALT)
    expected = entry.options.get(CONF_SETTINGS_PIN_HASH)
    if not salt or not expected:
        return False
    try:
        normalized = validate_pin_format(pin)
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            normalized.encode("utf-8"),
            bytes.fromhex(str(salt)),
            PIN_ITERATIONS,
        ).hex()
    except (TypeError, ValueError):
        return False
    return hmac.compare_digest(str(expected), actual)


def unlock_settings(
    hass: HomeAssistant,
    entry_id: str,
    user_id: str,
) -> None:
    """Unlock settings for one Home Assistant user for a limited period."""
    unlocks = hass.data.setdefault(DATA_SETTINGS_UNLOCKS, {})
    unlocks[(entry_id, user_id)] = time.monotonic() + SETTINGS_UNLOCK_SECONDS


def lock_settings(hass: HomeAssistant, entry_id: str, user_id: str) -> None:
    """Immediately revoke one user's settings unlock."""
    unlocks = hass.data.get(DATA_SETTINGS_UNLOCKS, {})
    unlocks.pop((entry_id, user_id), None)


def settings_are_unlocked(
    hass: HomeAssistant,
    entry_id: str,
    user_id: str | None,
) -> bool:
    """Return whether one user's backend settings unlock is still valid."""
    if not user_id:
        return False
    unlocks = hass.data.get(DATA_SETTINGS_UNLOCKS, {})
    expires = unlocks.get((entry_id, user_id))
    if expires is None:
        return False
    if float(expires) <= time.monotonic():
        unlocks.pop((entry_id, user_id), None)
        return False
    return True


def clear_entry_unlocks(hass: HomeAssistant, entry_id: str) -> None:
    """Revoke all temporary unlocks for one config entry."""
    unlocks = hass.data.get(DATA_SETTINGS_UNLOCKS, {})
    for key in [key for key in unlocks if key[0] == entry_id]:
        unlocks.pop(key, None)
