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
        self, hass, account_id, serial, api, type="inverter", device_name=None, polling=True
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

        if serial.startswith("EMS"):
            _LOGGER.info("Setting up EMS {}, will always poll".format(serial))
            self.polling = True
        else:
            self.polling = polling

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
            info = await self.api.async_get_device_info(self.serial)
            if info or first:
                self.data["info"] = info
            status = await self.api.async_get_inverter_status(self.serial)
            if status or first:
                self.data["status"] = status
            meter = await self.api.async_get_inverter_meter(self.serial)
            if meter or first:
                self.data["meter"] = meter

            # Update registers every 5 minutes, other data every minute
            if first or (self.update_count == 0) or (self.polling and (self.update_count % 5) == 0):
                settings = await self.api.async_get_inverter_settings(self.serial, first=first, previous=self.data.get("settings", {}))
                if settings or first:
                    self.data["settings"] = settings

        if self.type == "smart_device":
            if first or (self.update_count == 0) or (self.polling and (self.update_count % 5) == 0):
                smart_device = await self.api.async_get_smart_device(self.serial)
                if smart_device or first:
                    self.data["smart_device"] = smart_device
            point = await self.api.async_get_smart_device_data(self.serial)
            if point or first:
                self.data["point"] = point

        if self.type == "evc_device":
            evc_device = await self.api.async_get_evc_device(self.serial)
            if evc_device or first:
                self.data["evc_device"] = evc_device
            evc_point = await self.api.async_get_evc_device_data(self.serial)
            if evc_point or first:
                self.data["evc_point"] = evc_point

            if first or (self.update_count == 0) or (self.polling and (self.update_count % 10) == 0):
                sessions = await self.api.async_get_evc_sessions(self.serial)
                if sessions or first:
                    self.data["sessions"] = sessions

            if first or (self.update_count == 0) or (self.polling and (self.update_count % 5) == 0):
                commands = await self.api.async_get_evc_commands(self.serial)
                if commands or first:
                    self.data["commands"] = commands

        _LOGGER.info("Coordinator data Update for device {}".format(self.device_name))
        if not first:
            self.update_count += 1
        return self.data


async def async_setup_cloud_coordinator(
    hass, account_id: str, serial, type="inverter", device_name=None, polling=True
):
    hass.data[DOMAIN][account_id][DATA_SERIALS][serial][DATA_ACCOUNT_COORDINATOR] = (
        CloudCoordinator(
            hass,
            account_id,
            serial,
            hass.data[DOMAIN][account_id][DATA_CLIENT],
            type=type,
            device_name=device_name,
            polling=polling,
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
