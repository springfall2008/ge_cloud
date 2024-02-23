from .const import (
    GE_API_INVERTER_STATUS,
    GE_API_URL,
    GE_API_DEVICES,
    GE_API_INVERTER_METER,
    GE_API_INVERTER_SETTINGS,
    GE_API_INVERTER_READ_SETTING,
    GE_API_INVERTER_WRITE_SETTING,
    GE_API_INVERTER_SETTING_SUPPORTED
)

import requests
import json
import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

class GECloudApiClient:
    def __init__(self, account_id, api_key):
        """
        Setup client
        """
        self.account_id = account_id
        self.api_key = api_key
        self.register_list = None

    async def async_read_inverter_setting(self, serial, setting_id):
        """
        Read a setting from the inverter
        """
        if setting_id in GE_API_INVERTER_SETTING_SUPPORTED:
            data = await self.async_get_inverter_data(GE_API_INVERTER_READ_SETTING, serial, setting_id, post=True)
            _LOGGER.info("Got setting id {} data {}".format(setting_id, data))
            return data
        return None

    async def async_write_inverter_setting(self, serial, setting_id, value):
        """
        Write a setting to the inverter
        """
        if setting_id in GE_API_INVERTER_SETTING_SUPPORTED:
            data = await self.async_get_inverter_data(GE_API_INVERTER_WRITE_SETTING, serial, setting_id, post=True, datain={"value": str(value), "context" : "homeassistant"})
            _LOGGER.info("Write setting id {} value {} returns {}".format(setting_id, value, data))
            return data
        return None

    async def async_get_inverter_settings(self, serial):
        """
        Get settings for account
        """
        if not self.register_list:
            self.register_list = await self.async_get_inverter_data(GE_API_INVERTER_SETTINGS, serial)
        results = {}
        if self.register_list:
            for setting in self.register_list:
                sid = setting.get('id', None)
                name = setting.get('name', None)
                validation_rules = setting.get('validation_rules', None)
                if sid and name:
                    data = await self.async_read_inverter_setting(serial, sid)
                    if data and 'value' in data:
                        value = data['value']
                        _LOGGER.info("Setting id {} data {} name {} value {}".format(sid, data, name, value))
                        results[sid] = {'name': name, 'value': value, 'validation_rules': validation_rules}
        return results

    async def async_get_devices(self):
        """
        Get list of inverters
        """
        device_list = await self.async_get_inverter_data(GE_API_DEVICES)
        serials = []
        if device_list is not None:
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
        """
        Get basis status for inverter
        """
        return await self.async_get_inverter_data(GE_API_INVERTER_STATUS, serial)

    async def async_get_inverter_meter(self, serial):
        """
        Get meter data for inverter
        """
        return await self.async_get_inverter_data(GE_API_INVERTER_METER, serial)

    async def async_get_inverter_data(self, endpoint, serial="", setting_id="", post=False, datain=None):
        """
        Basic API call to GE Cloud
        """
        url = GE_API_URL + endpoint.format(inverter_serial_number=serial, setting_id=setting_id)
        headers = {
            "Authorization": "Bearer " + self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        _LOGGER.info("GE Cloud API call url {} data {}".format(url, datain))
        if post:
            if datain:
                response = await asyncio.to_thread(requests.post, url, headers=headers, json=datain)
            else:
                response = await asyncio.to_thread(requests.post, url, headers=headers)
        else:
            response = await asyncio.to_thread(requests.get, url, headers=headers)
        try:
            data = response.json()
        except requests.exceptions.JSONDecodeError:
            data = None
            _LOGGER.error("Failed to decode response from {}".format(url))
        _LOGGER.info("Got response from {} data {}".format(url, data))
        if data and 'data' in data:
            data = data['data']
        else:
            data = None
        return data