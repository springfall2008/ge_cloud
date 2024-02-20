import voluptuous as vol
import logging

from homeassistant.config_entries import ConfigFlow, OptionsFlow
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
    DATA_SCHEMA_ACCOUNT,
    CONFIG_ACCOUNT_ID,
)

_LOGGER = logging.getLogger(__name__)


async def async_validate_main_config(data):
    """
    Validate the main configuration

    data: dict
    """
    errors = {}

    if 0:
        client = OctopusEnergyApiClient(data[CONFIG_MAIN_API_KEY])

        try:
            account_info = await client.async_get_account(data[CONFIG_ACCOUNT_ID])
        except RequestException:
            # Treat errors as not finding the account
            account_info = None
        except ServerException:
            errors[CONFIG_MAIN_API_KEY] = "server_error"

        if CONFIG_MAIN_API_KEY not in errors and account_info is None:
            errors[CONFIG_MAIN_API_KEY] = "account_not_found"

    return errors


class GECloudConfigFlow(ConfigFlow, domain=DOMAIN):
    """Example config flow."""

    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes
    VERSION = CONFIG_VERSION

    async def async_step_account(self, user_input):
        """Setup the initial account based on the provided user input"""
        errors = await async_validate_main_config(user_input)

        if len(errors) < 1:
            user_input[CONFIG_KIND] = CONFIG_KIND_ACCOUNT
            return self.async_create_entry(
                title=user_input[CONFIG_ACCOUNT_ID], data=user_input
            )

        return self.async_show_form(
            step_id="account", data_schema=DATA_SCHEMA_ACCOUNT, errors=errors
        )

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

        return self.async_show_form(step_id="account", data_schema=DATA_SCHEMA_ACCOUNT)
