import voluptuous as vol
import homeassistant.helpers.config_validation as cv

DOMAIN = "ge_cloud"
INTEGRATION_VERSION = "1.0.0"
CONFIG_VERSION = 1

CONFIG_KIND = "kind"
CONFIG_KIND_ACCOUNT = "account"

DATA_CONFIG = "CONFIG"
DATA_CLIENT = "DATA_CLIENT"
DATA_ACCOUNT = "ACCOUNT"
DATA_SERIALS = "SERIALS"
DATA_ACCOUNT_COORDINATOR = "ACCOUNT_COORDINATOR"
CONFIG_MAIN_API_KEY = "api_key"
CONFIG_ACCOUNT_ID = "account_id"

DATA_SCHEMA_ACCOUNT = {
  vol.Required(CONFIG_ACCOUNT_ID, default="home"): str,
  vol.Required(CONFIG_MAIN_API_KEY, default="api_key"): str
}

GE_API_URL = "https://api.givenergy.cloud/v1/"
GE_API_INVERTER_STATUS = "inverter/{inverter_serial_number}/system-data/latest"
GE_API_INVERTER_METER = "inverter/{inverter_serial_number}/meter-data/latest"
GE_API_DEVICES = "communication-device"
