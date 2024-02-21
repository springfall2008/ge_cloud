from .const import (GE_API_INVERTER_STATUS, GE_API_URL, GE_API_DEVICES)

import requests
import json
import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

class GECloudApiClient:
    def __init__(self, account_id, api_key):
        self.account_id = account_id
        self.api_key = api_key

    async def async_get_devices(self):
        data = await self.async_get_inverter_data(GE_API_DEVICES)
        serials = []
        if data is not None:
            if 'data' in data:
                device_list = data['data']
                _LOGGER.info("Got device list {}".format(device_list))
                for device in device_list:
                    _LOGGER.info("Device {}".format(device))
                    inverter = device.get('inverter', None)
                    if inverter:
                        _LOGGER.info("Got inverter {}".format(inverter))
                        serial = inverter.get('serial', None)
                        if serial:
                            _LOGGER.info("Got serial {}".format(serial))
                            serials.append(serial)

        return serials
    async def async_get_inverter_status(self, serial):
        data = await self.async_get_inverter_data(GE_API_INVERTER_STATUS, serial)
        if data is not None:
            if 'data' in data:
                return data['data']
        return None

    async def async_get_inverter_data(self, endpoint, serial=""):
        url = GE_API_URL + endpoint.format(inverter_serial_number=serial)
        headers = {
            "Authorization": "Bearer " + self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        _LOGGER.info("Getting inverter status from {}".format(url))
        response = await asyncio.to_thread(requests.get, url, headers=headers)
        try:
            data = response.json()
        except requests.exceptions.JSONDecodeError:
            data = None
            _LOGGER.error("Failed to decode response from {}".format(url))

        _LOGGER.info("Got response {} decoded {}".format(response, data))
        return data