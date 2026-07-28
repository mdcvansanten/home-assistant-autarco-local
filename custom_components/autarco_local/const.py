"""Constants for Autarco Local."""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "autarco_local"

DEFAULT_NAME: Final = "Autarco Local"
DEFAULT_PORT: Final = 502
DEFAULT_DEVICE_ID: Final = 1
DEFAULT_SCAN_INTERVAL: Final = 30
DEFAULT_TIMEOUT: Final = 5

MIN_SCAN_INTERVAL: Final = 10
MAX_SCAN_INTERVAL: Final = 3600
MIN_TIMEOUT: Final = 1
MAX_TIMEOUT: Final = 30

CONF_DEVICE_ID: Final = "device_id"
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_TIMEOUT: Final = "timeout"

PLATFORMS: Final = ["sensor"]

# A Modbus request may contain at most 125 registers.
REGISTER_BLOCKS: Final = (
    (33000, 125),
    (33125, 15),
)

DEFAULT_UPDATE_INTERVAL: Final = timedelta(seconds=DEFAULT_SCAN_INTERVAL)
