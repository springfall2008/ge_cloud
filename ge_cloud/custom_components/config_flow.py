import voluptuous as vol
import logging

from homeassistant.config_entries import (ConfigFlow, OptionsFlow)
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import selector
from homeassistant.components.sensor import (
  SensorDeviceClass,
)
from .const import (
    CONFIG_MAIN_API_KEY,
    DOMAIN,
    CONFIG_VERSION,
    CONFIG_KIND,
    CONFIG_KIND_ACCOUNT,
    DATA_SCHEMA_ACCOUNT
)

_LOGGER = logging.getLogger(__name__)

class GECloudConfigFlow(ConfigFlow, domain=DOMAIN):
    """Example config flow."""
    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes
    VERSION = CONFIG_VERSION

    # The schema of the config flow
    async def async_step_user(self, user_input):
        is_account_setup = False
        for entry in self._async_current_entries(include_ignore=False):
            if CONFIG_MAIN_API_KEY in entry.data:
                is_account_setup = True
                break

        if user_input is not None:
            if CONFIG_KIND in user_input:
                if user_input[CONFIG_KIND] == CONFIG_KIND_ACCOUNT:
                    return await self.async_step_account(user_input)            
            
            return self.async_abort(reason="unexpected_entry")

        if is_account_setup:
            return   

        return self.async_show_form(
            step_id="account", data_schema=DATA_SCHEMA_ACCOUNT
        )