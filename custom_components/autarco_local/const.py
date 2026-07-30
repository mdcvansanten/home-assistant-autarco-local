"""Constants for Autarco Local."""
from typing import Final
DOMAIN: Final = "autarco_local"
DEFAULT_NAME: Final = "Autarco Local"
DEFAULT_PORT: Final = 502
DEFAULT_DEVICE_ID: Final = 1
DEFAULT_SCAN_INTERVAL: Final = 30
DEFAULT_TIMEOUT: Final = 5
DEFAULT_RETRIES: Final = 2
FAILURE_THRESHOLD: Final = 3
MIN_SCAN_INTERVAL: Final = 10
MAX_SCAN_INTERVAL: Final = 3600
MIN_TIMEOUT: Final = 1
MAX_TIMEOUT: Final = 30
MIN_RETRIES: Final = 0
MAX_RETRIES: Final = 5
CONF_DEVICE_ID: Final = "device_id"
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_TIMEOUT: Final = "timeout"
CONF_RETRIES: Final = "retries"
PLATFORMS: Final = ["binary_sensor", "sensor"]
REGISTER_START: Final = 33000
REGISTER_END: Final = 33170
REGISTER_CHUNK_SIZE: Final = 10
VALIDATION_REGISTER_START: Final = 33000
VALIDATION_REGISTER_COUNT: Final = 10
