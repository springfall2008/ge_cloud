from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util
from homeassistant.util.dt import (now)

import voluptuous as vol
import logging
from datetime import datetime, timedelta

from .const import(DOMAIN, CONFIG_ACCOUNT_ID, CONFIG_MAIN_API_KEY, DATA_CLIENT, DATA_ACCOUNT, DATA_ACCOUNT_COORDINATOR)
from .api import GECloudApiClient

_LOGGER = logging.getLogger(__name__)

class CloudCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass, account_id, api):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="GE Cloud Update",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=60),
            always_update=True,
        )
        self.api = api
        self.account_id = account_id
        self.data = {}
        _LOGGER.info("Coordinator class created for account {}".format(account_id))

    async def force_update(self):
        """
        Force update of data
        """
        await self._async_update_data()

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        _LOGGER.info("Coordinator data Update")
        status = await self.api.async_get_inverter_status()
        self.data["status"] = status
        _LOGGER.info("Coordinator data returned status {}".format(status))
        return self.data

async def async_setup_cloud_coordinator(hass, account_id: str):

    _LOGGER.info("Create Cloud coordinator now for account {}".format(account_id))
    hass.data[DOMAIN][account_id][DATA_ACCOUNT_COORDINATOR] = CloudCoordinator(hass, account_id, hass.data[DOMAIN][account_id][DATA_CLIENT])
    _LOGGER.info("Create Cloud coordinator created for account {}".format(account_id))
    await hass.data[DOMAIN][account_id][DATA_ACCOUNT_COORDINATOR].force_update()
