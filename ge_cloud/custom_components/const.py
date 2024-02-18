import voluptuous as vol
import homeassistant.helpers.config_validation as cv

DOMAIN = "ge_cloud"
INTEGRATION_VERSION = "1.0.0"
CONFIG_VERSION = 1

CONFIG_KIND = "kind"
CONFIG_KIND_ACCOUNT = "account"

DATA_CONFIG = "CONFIG"
CONFIG_MAIN_API_KEY = "api_key"
CONFIG_ACCOUNT_ID = "account_id"

DATA_SCHEMA_ACCOUNT = vol.Schema({
  vol.Required(CONFIG_ACCOUNT_ID): str,
  vol.Required(CONFIG_MAIN_API_KEY): str
})