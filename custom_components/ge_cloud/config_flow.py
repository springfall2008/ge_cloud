import voluptuous as vol
import logging

from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import selector
from homeassistant.components.sensor import (
    SensorDeviceClass,
)
from homeassistant import config_entries, exceptions
from homeassistant.core import HomeAssistant

from .const import (
    CONFIG_MAIN_API_KEY,
    DOMAIN,
    CONFIG_VERSION,
    CONFIG_KIND,
    CONFIG_KIND_ACCOUNT,
    DATA_SCHEMA_ACCOUNT,
    CONFIG_ACCOUNT_ID,
    CONFIG_INVERTER_ENABLE,
    CONFIG_SMART_DEVICE_ENABLE,
    CONFIG_EVC_ENABLE,
    CONFIG_POLL_INVERTER,
)
from .api import GECloudApiClient

_LOGGER = logging.getLogger(__name__)


async def async_validate_main_config(data):
    """
    Validate the main configuration

    data: dict
    """
    errors = {}

    account_id = data[CONFIG_ACCOUNT_ID]
    api_key = data[CONFIG_MAIN_API_KEY]
    inverter_enable = data[CONFIG_INVERTER_ENABLE]
    smart_device_enable = data[CONFIG_SMART_DEVICE_ENABLE]
    evc_enable = data[CONFIG_EVC_ENABLE]
    poll_inverter = data[CONFIG_POLL_INVERTER]
    _LOGGER.info(
        "Validating main config for account {} api_key {}".format(account_id, api_key)
    )
    api = GECloudApiClient(account_id, api_key)
    inverter_serials = []
    smart_devices = []
    evc_devices = []

    if inverter_enable:
        inverter_serials = await api.async_get_devices()
        _LOGGER.info("Got inverter serials {}".format(inverter_serials))
    if smart_device_enable:
        smart_devices = await api.async_get_smart_devices()
        _LOGGER.info("Got smart devices {}".format(smart_devices))
    if evc_enable:
        evc_devices = await api.async_get_evc_devices()
        _LOGGER.info("Got evc_devices {}".format(evc_devices))

    if not inverter_serials and not smart_devices and not evc_devices:
        errors[CONFIG_MAIN_API_KEY] = "invalid_api_key"
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
            step_id="account",
            data_schema=vol.Schema(DATA_SCHEMA_ACCOUNT),
            errors=errors,
        )

    # The schema of the config flow
    async def async_step_user(self, user_input=None):
        return self.async_show_form(
            step_id="account", data_schema=vol.Schema(DATA_SCHEMA_ACCOUNT)
        )
