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

# Runtime/input registers used by the existing monitoring layer.
REGISTER_START: Final = 33000
REGISTER_END: Final = 33170
REGISTER_CHUNK_SIZE: Final = 10
VALIDATION_REGISTER_START: Final = 33000
VALIDATION_REGISTER_COUNT: Final = 10

# Read-only holding-register blocks used by the v0.5 settings layer.
# Blocks are deliberately narrow so an unsupported setting family cannot affect
# the stable 33xxx monitoring poll. No Modbus write functions are implemented.
SETTING_REGISTER_BLOCKS: Final = (
    (43010, 2),   # overcharge / overdischarge SOC
    (43018, 1),   # force-charge SOC
    (43024, 5),   # reserve SOC / force-charge power limit (+ adjacent values)
    (43110, 1),   # storage-mode bit field
    (43137, 14),  # off-grid SOC, charge/discharge current and time slot 1
    (43153, 8),   # time slot 2
    (43163, 8),   # time slot 3
)
