import voluptuous as vol
import homeassistant.helpers.config_validation as cv

DOMAIN = "ge_cloud"
INTEGRATION_VERSION = "1.0.4"
CONFIG_VERSION = 1

CONFIG_KIND = "kind"
CONFIG_KIND_ACCOUNT = "account"

DATA_CONFIG = "CONFIG"
DATA_CLIENT = "DATA_CLIENT"
DATA_ACCOUNT = "ACCOUNT"
DATA_SERIALS = "SERIALS"
DATA_SMART_DEVICES = "SMART_DEVICES"
DATA_ACCOUNT_COORDINATOR = "ACCOUNT_COORDINATOR"
CONFIG_MAIN_API_KEY = "api_key"
CONFIG_ACCOUNT_ID = "account_id"

DATA_SCHEMA_ACCOUNT = {
    vol.Required(CONFIG_ACCOUNT_ID, default="home"): str,
    vol.Required(CONFIG_MAIN_API_KEY, default="api_key"): str,
}

GE_API_URL = "https://api.givenergy.cloud/v1/"
GE_API_INVERTER_STATUS = "inverter/{inverter_serial_number}/system-data/latest"
GE_API_INVERTER_METER = "inverter/{inverter_serial_number}/meter-data/latest"
GE_API_INVERTER_SETTINGS = "inverter/{inverter_serial_number}/settings"
GE_API_INVERTER_READ_SETTING = (
    "inverter/{inverter_serial_number}/settings/{setting_id}/read"
)
GE_API_INVERTER_WRITE_SETTING = (
    "inverter/{inverter_serial_number}/settings/{setting_id}/write"
)
GE_API_DEVICES = "communication-device"
GE_API_SMART_DEVICES = "smart-device"
GE_API_SMART_DEVICE = "smart-device/{uuid}"
GE_API_SMART_DEVICE_DATA = "smart-device/{uuid}/data"
GE_API_INVERTER_SETTING_SUPPORTED = [
    17,
    24,
    47,
    53,
    54,
    56,
    64,
    65,
    66,
    71,
    72,
    73,
    75,
    77,
    267,
    268,
    380,
    384,
    385,
    386,
    387,
    388,
    389,
    390,
    391,
    392,
    393,
    394,
    395,
    396,
    397,
    398,
    399,
    400,
    401,
    402,
    403,
    404,
    405,
    406,
    407,
    408,
    409,
    410,
]
GE_REGISTER_BATTERY_CUTOFF_LIMIT = 75
