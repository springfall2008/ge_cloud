from .const import (
    GE_API_INVERTER_STATUS,
    GE_API_URL,
    GE_API_DEVICES,
    GE_API_INVERTER_METER,
    GE_API_INVERTER_SETTINGS,
    GE_API_INVERTER_READ_SETTING,
    GE_API_INVERTER_WRITE_SETTING,
    GE_API_INVERTER_SETTING_SUPPORTED,
    GE_API_SMART_DEVICES,
    GE_API_SMART_DEVICE,
    GE_API_SMART_DEVICE_DATA
)

import requests
import json
import asyncio
import logging

_LOGGER = logging.getLogger(__name__)
TIMEOUT = 30
RETRIES = 5

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
            for retry in range(RETRIES):
                data = await self.async_get_inverter_data(GE_API_INVERTER_READ_SETTING, serial, setting_id, post=True)
                # -1 is a bad value
                if data.get('value', -1) == -1:
                    data = None
                if data:
                    break
            _LOGGER.info("Got setting id {} data {}".format(setting_id, data))
            return data
        return None

    async def async_write_inverter_setting(self, serial, setting_id, value):
        """
        Write a setting to the inverter
        """
        if setting_id in GE_API_INVERTER_SETTING_SUPPORTED:
            for retry in range(RETRIES):
                data = await self.async_get_inverter_data(GE_API_INVERTER_WRITE_SETTING, serial, setting_id, post=True, datain={"value": str(value), "context" : "homeassistant"})
                _LOGGER.info("Write setting id {} value {} returns {}".format(setting_id, value, data))
                if 'success' in data:
                    if not data['success']:
                        data = None
                if data:
                    break
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

    async def async_get_smart_device_data(self, uuid):
        """
        Get smart device data points
        """
        data = await self.async_get_inverter_data(GE_API_SMART_DEVICE_DATA, uuid=uuid)
        for point in data:
            _LOGGER.info("Smart device point {}".format(point))
            return point
        return {}

    async def async_get_smart_device(self, uuid):
        """
        Get smart device
        """
        device = await self.async_get_inverter_data(GE_API_SMART_DEVICE, uuid=uuid)
        _LOGGER.info("Device {}".format(device))
        if device:
            uuid = device.get('uuid', None)
            other_data = device.get('other_data', {})
            alias = device.get('alias', None)
            local_key = other_data.get('local_key', None)
            asset_id = other_data.get('asset_id', None)
            hardware_id = other_data.get('hardware_id', None)
            _LOGGER.info("Got smart device uuid {} alias {} local_key {} asset_id {} hardware_id {}".format(uuid, alias, local_key, asset_id, hardware_id))
            return {'uuid': uuid, 'alias': alias, 'local_key': local_key, 'asset_id': asset_id, 'hardware_id': hardware_id}
        return {}

    async def async_get_smart_devices(self):
        """
        Get list of smart devices
        """
        device_list = await self.async_get_inverter_data(GE_API_SMART_DEVICES)
        devices = []
        if device_list is not None:
            _LOGGER.info("Got smart device list {}".format(device_list))
            for device in device_list:
                _LOGGER.info("Device {}".format(device))
                uuid = device.get('uuid', None)
                other_data = device.get('other_data', {})
                alias = device.get('alias', None)
                local_key = other_data.get('local_key', None)
                _LOGGER.info("Got smart device uuid {} alias {} local_key {}".format(uuid, alias, local_key))
                devices.append({'uuid': uuid, 'alias': alias, 'local_key': local_key})
        return devices

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

    async def async_get_inverter_data(self, endpoint, serial="", setting_id="", post=False, datain=None, uuid=""):
        """
        Basic API call to GE Cloud
        """
        url = GE_API_URL + endpoint.format(inverter_serial_number=serial, setting_id=setting_id, uuid=uuid)
        headers = {
            "Authorization": "Bearer " + self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        _LOGGER.info("GE Cloud API call url {} data {}".format(url, datain))
        if post:
            if datain:
                response = await asyncio.to_thread(requests.post, url, headers=headers, json=datain, timeout=TIMEOUT)
            else:
                response = await asyncio.to_thread(requests.post, url, headers=headers, timeout=TIMEOUT)
        else:
            response = await asyncio.to_thread(requests.get, url, headers=headers, timeout=TIMEOUT)
        try:
            data = response.json()
        except requests.exceptions.JSONDecodeError:
            _LOGGER.error("Failed to decode response from {}".format(url))
            data = None
        except requests.Timeout:
            _LOGGER.error("Timeout from {}".format(url))
            data = None

        # Check data
        if data and 'data' in data:
            data = data['data']
        else:
            data = None
        if response.status_code in [200, 201]:
            return data
        _LOGGER.error("Failed to get data from {} code {}".format(url, response.status_code))
        return None