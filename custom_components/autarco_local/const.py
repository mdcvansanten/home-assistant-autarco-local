"""Constants for Autarco Local."""

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

# The logger rejects one large 125-register request with exception code 2.
# Read the range in smaller chunks and skip unsupported holes.
REGISTER_START: Final = 33000
REGISTER_END: Final = 33139
REGISTER_CHUNK_SIZE: Final = 10

# Small, previously confirmed readable range used during config validation.
VALIDATION_REGISTER_START: Final = 33000
VALIDATION_REGISTER_COUNT: Final = 10
