from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util
from homeassistant.util.dt import now

import voluptuous as vol
import logging
from datetime import datetime, timedelta

from .const import (
    DOMAIN,
    CONFIG_ACCOUNT_ID,
    CONFIG_MAIN_API_KEY,
    DATA_CLIENT,
    DATA_ACCOUNT,
    DATA_ACCOUNT_COORDINATOR,
    DATA_SERIALS,
)
from .api import GECloudApiClient

_LOGGER = logging.getLogger(__name__)


class CloudCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(
        self, hass, account_id, serial, api, type="inverter", device_name=None
    ):
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
        self.account_id = account_id
        self.api = api
        self.serial = serial
        self.type = type
        self.data = {}
        self.update_count = 0

        if device_name:
            self.device_name = device_name
        else:
            self.device_name = serial

    async def first_update(self):
        """
        Force update of data
        """
        return await self._async_update_data(first=True)

    async def _async_update_data(self, first=False):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        if self.type == "inverter":
            self.data["info"] = await self.api.async_get_device_info(self.serial)
            self.data["status"] = await self.api.async_get_inverter_status(self.serial)
            self.data["meter"] = await self.api.async_get_inverter_meter(self.serial)
            # Update registers every 5 minutes, other data every minute
            if (self.update_count % 5) == 0:
                self.data["settings"] = await self.api.async_get_inverter_settings(
                    self.serial, first=first, previous=self.data.get("settings", {})
                )
        if self.type == "smart_device":
            if (self.update_count % 5) == 0:
                self.data["smart_device"] = await self.api.async_get_smart_device(
                    self.serial
                )
            self.data["point"] = await self.api.async_get_smart_device_data(self.serial)

        if self.type == "evc_device":
            self.data["evc_device"] = await self.api.async_get_evc_device(self.serial)
            self.data["point"] = await self.api.async_get_evc_device_data(self.serial)
            if (self.update_count % 5) == 0:
                self.data["commands"] = await self.api.async_get_evc_commands(self.serial)
            if (self.update_count % 10) == 0:
                self.data["sessions"] = await self.api.async_get_evc_sessions(self.serial)

        _LOGGER.info("Coordinator data Update for device {}".format(self.device_name))
        if not first:
            self.update_count += 1
        return self.data


async def async_setup_cloud_coordinator(
    hass, account_id: str, serial, type="inverter", device_name=None
):
    hass.data[DOMAIN][account_id][DATA_SERIALS][serial][DATA_ACCOUNT_COORDINATOR] = (
        CloudCoordinator(
            hass,
            account_id,
            serial,
            hass.data[DOMAIN][account_id][DATA_CLIENT],
            type=type,
            device_name=device_name,
        )
    )
    _LOGGER.info(
        "Create Cloud coordinator created for account {} serial".format(
            account_id, serial
        )
    )
    await hass.data[DOMAIN][account_id][DATA_SERIALS][serial][
        DATA_ACCOUNT_COORDINATOR
    ].first_update()
