from .const import (GE_API_INVERTER_STATUS, GE_API_URL)

import requests
import json
import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

class GECloudApiClient:
    def __init__(self, serial, api_key):
        self.serial = serial
        self.api_key = api_key

    async def async_get_inverter_status(self):
        data = await self.async_get_inverter_data(GE_API_INVERTER_STATUS)
        if data is not None:
            if 'data' in data:
                return data['data']
        return None

    async def async_get_inverter_data(self, endpoint):
        url = GE_API_URL + endpoint.format(inverter_serial_number=self.serial)
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