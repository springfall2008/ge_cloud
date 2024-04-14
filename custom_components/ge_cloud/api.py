from .const import (
    GE_API_INVERTER_STATUS,
    GE_API_URL,
    GE_API_DEVICES,
    GE_API_INVERTER_METER,
    GE_API_INVERTER_SETTINGS,
    GE_API_INVERTER_READ_SETTING,
    GE_API_INVERTER_WRITE_SETTING,
    GE_API_SMART_DEVICES,
    GE_API_SMART_DEVICE,
    GE_API_SMART_DEVICE_DATA,
    GE_API_DEVICE_INFO,
)

import requests
import json
import asyncio
import logging
import random

_LOGGER = logging.getLogger(__name__)
TIMEOUT = 240
RETRIES = 20


class GECloudApiClient:
    def __init__(self, account_id, api_key):
        """
        Setup client
        """
        self.account_id = account_id
        self.api_key = api_key
        self.register_list = {}

    async def async_read_inverter_setting(self, serial, setting_id):
        """
        Read a setting from the inverter
        """
        for retry in range(RETRIES):
            data = await self.async_get_inverter_data(
                GE_API_INVERTER_READ_SETTING, serial, setting_id, post=True
            )
            # -1 is a bad value
            if data and data.get("value", -1) == -1:
                data = None
            elif data and data.get("value", -1) == -2:
                data = None
            if data:
                break
            await asyncio.sleep(1 * (retry + 1))
        if data is None:
            _LOGGER.error("Failed to read setting id {}".format(setting_id))
        else:
            _LOGGER.info("Got setting id {} data {}".format(setting_id, data))
        return data

    async def async_write_inverter_setting(self, serial, setting_id, value):
        """
        Write a setting to the inverter
        """
        for retry in range(RETRIES):
            await asyncio.sleep(0.2 * (retry + 1))
            data = await self.async_get_inverter_data(
                GE_API_INVERTER_WRITE_SETTING,
                serial,
                setting_id,
                post=True,
                datain={"value": str(value), "context": "homeassistant"},
            )
            _LOGGER.info(
                "Write setting id {} value {} returns {}".format(
                    setting_id, value, data
                )
            )
            if "success" in data:
                if not data["success"]:
                    data = None
            if data:
                break
            await asyncio.sleep(0.5 * (retry + 1))
        if data is None:
            _LOGGER.error(
                "Failed to write setting id {} value {}".format(setting_id, value)
            )
        return data

    async def async_get_inverter_settings(self, serial, previous={}):
        """
        Get settings for account
        """
        if serial not in self.register_list:
            self.register_list[serial] = await self.async_get_inverter_data_retry(
                GE_API_INVERTER_SETTINGS, serial
            )
            _LOGGER.info(
                "Register list for serial {} is {}".format(
                    serial, self.register_list[serial]
                )
            )
        results = previous.copy()
        if serial in self.register_list:
            # Async read for all the registers
            futures = []
            loop = asyncio.get_running_loop()

            for setting in self.register_list[serial]:
                sid = setting.get("id", None)
                name = setting.get("name", None)

                validation_rules = setting.get("validation_rules", None)
                validation = setting.get("validation", None)
                if sid and name:
                    if "writeonly" in validation_rules:
                        results[sid] = {
                            "name": name,
                            "value": False,
                            "validation_rules": validation_rules,
                            "validation": validation,
                        }
                    else:
                        future = {}
                        future["sid"] = sid
                        future["name"] = name
                        future["data"] = loop.create_task(
                            self.async_read_inverter_setting(serial, sid)
                        )
                        future["validation_rules"] = validation_rules
                        future["validation"] = validation
                        futures.append(future)
                        await asyncio.sleep(1)

            # Wait for all the futures to complete and store results
            for future in futures:
                sid = future["sid"]
                name = future["name"]
                validation_rules = future["validation_rules"]
                validation = future["validation"]
                data = await future["data"]
                if data and ("value" in data):
                    value = data["value"]
                    _LOGGER.info(
                        "Setting id {} data {} name {} value {}".format(
                            sid, data, name, value
                        )
                    )
                    if value is not None:
                        results[sid] = {
                            "name": name,
                            "value": value,
                            "validation_rules": validation_rules,
                            "validation": validation,
                        }
        return results

    async def async_get_smart_device_data(self, uuid):
        """
        Get smart device data points
        """
        data = await self.async_get_inverter_data_retry(
            GE_API_SMART_DEVICE_DATA, uuid=uuid
        )
        for point in data:
            _LOGGER.info("Smart device point {}".format(point))
            return point
        return {}

    async def async_get_smart_device(self, uuid):
        """
        Get smart device
        """
        device = await self.async_get_inverter_data_retry(
            GE_API_SMART_DEVICE, uuid=uuid
        )
        _LOGGER.info("Device {}".format(device))
        if device:
            uuid = device.get("uuid", None)
            other_data = device.get("other_data", {})
            alias = device.get("alias", None)
            local_key = other_data.get("local_key", None)
            asset_id = other_data.get("asset_id", None)
            hardware_id = other_data.get("hardware_id", None)
            _LOGGER.info(
                "Got smart device uuid {} alias {} local_key {} asset_id {} hardware_id {}".format(
                    uuid, alias, local_key, asset_id, hardware_id
                )
            )
            return {
                "uuid": uuid,
                "alias": alias,
                "local_key": local_key,
                "asset_id": asset_id,
                "hardware_id": hardware_id,
            }
        return {}

    async def async_get_smart_devices(self):
        """
        Get list of smart devices
        """
        device_list = await self.async_get_inverter_data_retry(GE_API_SMART_DEVICES)
        devices = []
        if device_list is not None:
            for device in device_list:
                uuid = device.get("uuid", None)
                other_data = device.get("other_data", {})
                alias = device.get("alias", None)
                local_key = other_data.get("local_key", None)
                _LOGGER.info(
                    "Got smart device uuid {} alias {} local_key {}".format(
                        uuid, alias, local_key
                    )
                )
                devices.append({"uuid": uuid, "alias": alias, "local_key": local_key})
        return devices

    async def async_get_device_info(self, serial):
        """
        Get the device info
        """
        device_list = await self.async_get_inverter_data_retry(GE_API_DEVICE_INFO)
        if device_list is not None:
            for device in device_list:
                inverter = device.get("inverter", None)
                if inverter:
                    _LOGGER.info("Got inverter {}".format(inverter))
                    this_serial = inverter.get("serial", None)
                    if this_serial and this_serial == serial:
                        _LOGGER.info("Got device {} info {}".format(serial, inverter))
                        return inverter
        return None

    async def async_get_devices(self):
        """
        Get list of inverters
        """
        device_list = await self.async_get_inverter_data_retry(GE_API_DEVICES)
        serials = []
        if device_list is not None:
            _LOGGER.info("Got device list {}".format(device_list))
            for device in device_list:
                _LOGGER.info("Device {}".format(device))
                inverter = device.get("inverter", None)
                if inverter:
                    _LOGGER.info("Got inverter {}".format(inverter))
                    serial = inverter.get("serial", None)
                    if serial:
                        _LOGGER.info("Got serial {}".format(serial))
                        serials.append(serial)

        return serials

    async def async_get_inverter_status(self, serial):
        """
        Get basis status for inverter
        """
        return await self.async_get_inverter_data_retry(GE_API_INVERTER_STATUS, serial)

    async def async_get_inverter_meter(self, serial):
        """
        Get meter data for inverter
        """
        meter = await self.async_get_inverter_data_retry(GE_API_INVERTER_METER, serial)
        _LOGGER.info("Serial {} meter {}".format(serial, meter))
        return meter

    async def async_get_inverter_data_retry(
        self, endpoint, serial="", setting_id="", post=False, datain=None, uuid=""
    ):
        """
        Retry API call
        """
        for retry in range(RETRIES):
            data = await self.async_get_inverter_data(
                endpoint, serial, setting_id, post, datain, uuid
            )
            if data:
                break
            await asyncio.sleep(1 * (retry + 1))
        if data is None:
            _LOGGER.error("Failed to get data from {}".format(endpoint))
        return data

    async def async_get_inverter_data(
        self, endpoint, serial="", setting_id="", post=False, datain=None, uuid=""
    ):
        """
        Basic API call to GE Cloud
        """
        url = GE_API_URL + endpoint.format(
            inverter_serial_number=serial, setting_id=setting_id, uuid=uuid
        )
        headers = {
            "Authorization": "Bearer " + self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if post:
            if datain:
                response = await asyncio.to_thread(
                    requests.post, url, headers=headers, json=datain, timeout=TIMEOUT
                )
            else:
                response = await asyncio.to_thread(
                    requests.post, url, headers=headers, timeout=TIMEOUT
                )
        else:
            response = await asyncio.to_thread(
                requests.get, url, headers=headers, timeout=TIMEOUT
            )
        try:
            data = response.json()
        except requests.exceptions.JSONDecodeError:
            _LOGGER.error("Failed to decode response from {}".format(url))
            data = None
        except (requests.Timeout, requests.exceptions.ReadTimeout):
            _LOGGER.error("Timeout from {}".format(url))
            data = None

        # Check data
        if data and "data" in data:
            data = data["data"]
        else:
            data = None
        _LOGGER.info(
            "GE Cloud API call url {} data {} response {} data {}".format(
                url, datain, response.status_code, data
            )
        )
        if response.status_code in [200, 201]:
            return data
        if response.status_code == 429:
            # Rate limiting so wait up to 30 seconds
            await asyncio.sleep(random.random() * 30)
        return None
