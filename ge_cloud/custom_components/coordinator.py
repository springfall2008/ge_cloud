from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

import voluptuous as vol
import logging
from datetime import datetime, timedelta

from .const import(DOMAIN, CONFIG_ACCOUNT_ID, CONFIG_MAIN_API_KEY)
from .api import GECloudApiClient

_LOGGER = logging.getLogger(__name__)

class GECloudCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, account_id, api_key) -> None:
        """Initialize"""
        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=timedelta(minutes=1)
        )
        self._entry = entry
        _LOGGER.info("GECloudCoordinator initialized with entry {}".format(entry))
        _LOGGER.info("Start coorindator main config for account_id {} api_key {}".format(account_id, api_key))
        self._api = GECloudApiClient(account_id, api_key)

    async def _async_update_data(self):
        data = {}
        status = await self._api.async_get_inverter_status()
        data["status"] = status
        _LOGGER.info("Coordinator Got status {}".format(status))
        return data