"""Constants for Autarco Local."""

from datetime import timedelta

DOMAIN = "autarco_local"
DEFAULT_NAME = "Autarco Local"
DEFAULT_PORT = 502
DEFAULT_DEVICE_ID = 1
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_TIMEOUT = 5

CONF_DEVICE_ID = "device_id"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_TIMEOUT = "timeout"

PLATFORMS = ["sensor"]

REGISTER_BLOCKS = (
    (33000, 125),
    (33125, 15),
)

UPDATE_INTERVAL_MIN = timedelta(seconds=10)
