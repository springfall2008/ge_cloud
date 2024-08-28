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
    EVC_DATA_POINTS,
    EVC_METER_CHARGER,
    GE_API_EVC_DEVICES,
    GE_API_EVC_DEVICE,
    GE_API_EVC_DEVICE_DATA,
    GE_API_EVC_COMMANDS,
    GE_API_EVC_COMMAND_DATA,
    GE_API_EVC_SEND_COMMAND,
    GE_API_EVC_SESSIONS,
    EVC_BLACKLIST_COMMANDS
)

import requests
import json
import asyncio
import logging
import random
from datetime import datetime
from datetime import timedelta
from datetime import timezone

_LOGGER = logging.getLogger(__name__)
TIMEOUT = 240
RETRIES = 5
MAX_THREADS = 2


class GECloudApiClient:
    def __init__(self, account_id, api_key):
        """
        Setup client
        """
        self.account_id = account_id
        self.api_key = api_key
        self.register_list = {}

    async def async_send_evc_command(self, uuid, command, params):
        """
        Send a command to the EVC
        """
        for retry in range(RETRIES):
            data = await self.async_get_inverter_data(
                GE_API_EVC_SEND_COMMAND,
                uuid=uuid,
                command=command,
                post=True,
                datain=params,
            )
            _LOGGER.info(
                "Write EVC comamnd {} params {} returns {}".format(
                    command, params, data
                )
            )
            if data and "success" in data:
                if not data["success"]:
                    data = None
            if data:
                break
            await asyncio.sleep(1 * (retry + 1))
        if data is None:
            _LOGGER.error(
                "Failed to send EVC command {} params {}".format(command, params)
            )
        return data

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
                # Inverter timeout, try to spread requests out
                await asyncio.sleep(random.random() * 2)
            if data:
                break
            await asyncio.sleep(1 * (retry + 1))
        if data is None:
            _LOGGER.warning("Failed to read inverter setting id {}".format(setting_id))
        return data

    async def async_write_inverter_setting(self, serial, setting_id, value):
        """
        Write a setting to the inverter
        """
        for retry in range(RETRIES):
            data = await self.async_get_inverter_data(
                GE_API_INVERTER_WRITE_SETTING,
                serial,
                setting_id,
                post=True,
                datain={"value": str(value), "context": "homeassistant"},
            )
            _LOGGER.info(
                "Write inverter setting id {} value {} returns {}".format(
                    setting_id, value, data
                )
            )
            if data and "success" in data:
                if not data["success"]:
                    data = None
            if data:
                break
            await asyncio.sleep(1 * (retry + 1))
        if data is None:
            _LOGGER.error(
                "Failed to write setting id {} value {}".format(setting_id, value)
            )
        return data

    async def async_get_inverter_settings(self, serial, first=False, previous={}):
        """
        Get settings for account
        """
        if serial not in self.register_list:
            self.register_list[serial] = await self.async_get_inverter_data_retry(
                GE_API_INVERTER_SETTINGS, serial
            )
            _LOGGER.info(
                "Register list for inverter serial {} is {}".format(
                    serial, self.register_list[serial]
                )
            )
        results = previous.copy()

        if serial in self.register_list:
            # Async read for all the registers
            futures = []
            pending = []
            complete = []
            loop = asyncio.get_running_loop()

            # Create the read tasks
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
                        future["serial"] = serial
                        future["name"] = name
                        future["validation_rules"] = validation_rules
                        future["validation"] = validation
                        pending.append(future)

            # Perform all the reads in parallel
            while pending or futures:
                while len(futures) < MAX_THREADS and pending:
                    future = pending.pop(0)
                    if not first:
                        future["future"] = loop.create_task(
                            self.async_read_inverter_setting(
                                future["serial"], future["sid"]
                            )
                        )
                    futures.append(future)
                if futures:
                    future = futures.pop(0)
                    if first:
                        future["data"] = None
                    else:
                        future["data"] = await future["future"]
                    future["future"] = None
                    complete.append(future)
                if not first:
                    await asyncio.sleep(0.2)

            # Wait for all the futures to complete and store results
            for future in complete:
                sid = future["sid"]
                name = future["name"]
                validation_rules = future["validation_rules"]
                validation = future["validation"]
                data = future["data"]
                if data and ("value" in data):
                    value = data["value"]
                else:
                    value = None

                _LOGGER.info(
                    "Setting id {} data {} name {} value {}".format(
                        sid, data, name, value
                    )
                )
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

    async def async_get_evc_sessions(self, uuid):
        """
        Get list of EVC sessions
        """
        now = datetime.now(timezone.utc)
        start = now - timedelta(hours=24)
        start_time=start.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_time=now.strftime("%Y-%m-%dT%H:%M:%SZ")

        data = await self.async_get_inverter_data_retry(GE_API_EVC_SESSIONS, uuid=uuid, start_time=start_time, end_time=end_time)
        if isinstance(data, list):
            _LOGGER.info("EVC sessions {}".format(data))
            return data
        return None

    async def async_get_evc_device_data(self, uuid):
        """
        Get smart device data points
        """
        now = datetime.now(timezone.utc)
        start = now - timedelta(minutes=10)
        start_time=start.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_time=now.strftime("%Y-%m-%dT%H:%M:%SZ")

        data = await self.async_get_inverter_data_retry(
            GE_API_EVC_DEVICE_DATA, uuid=uuid, meter_ids=str(EVC_METER_CHARGER), start_time=start_time, end_time=end_time
        )
        result = {}
        if not data:
            return result

        for meter in data:
            meter_id = meter.get("meter_id", -1)
            if meter_id == EVC_METER_CHARGER:
                for point in meter.get("measurements", []):
                    measurand = point.get("measurand", None)
                    if (measurand is not None) and measurand in EVC_DATA_POINTS:
                        value = point.get("value", None)
                        unit = point.get("unit", None)
                        result[EVC_DATA_POINTS[measurand]] = value
        _LOGGER.info("EVC device point {}".format(result))
        return result

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

    async def async_get_evc_commands(self, uuid):
        """
        Get EVC commands
        """
        command_info = {}
        commands = await self.async_get_inverter_data_retry(GE_API_EVC_COMMANDS, uuid=uuid)
        # Not desirable command
        for command_drop in EVC_BLACKLIST_COMMANDS:
            if command_drop in commands:
                commands.remove(command_drop)

        # Get command data
        for command in commands:
            command_data = await self.async_get_inverter_data_retry(GE_API_EVC_COMMAND_DATA, command=command, uuid=uuid)
            command_info[command] = command_data
            _LOGGER.info("Command {} data {}".format(command, command_data))

        return command_info

    async def async_get_evc_device(self, uuid):
        """
        Get EVC device
        """
        device = await self.async_get_inverter_data_retry(GE_API_EVC_DEVICE, uuid=uuid)
        _LOGGER.info("Device {}".format(device))
        if device:
            uuid = device.get("uuid", None)
            alias = device.get("alias", None)
            serial_number = device.get("serial_number", None)
            online = device.get("online", None)
            went_offline_at = device.get("went_offline_at", None)
            status = device.get("status", None)
            type = device.get("type", None)
            _LOGGER.info(
                "Got smart device uuid {} alias {} serial_number {} status {} online {} went_offline_at {} type {}".format(
                    uuid, alias, serial_number, status, online, went_offline_at, type
                )
            )
            return {
                "uuid": uuid,
                "alias": alias,
                "serial_number": serial_number,
                "status": status,
                "online": online,
                "type": type,
                "went_offline_at": went_offline_at
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

    async def async_get_evc_devices(self):
        """
        Get list of smart devices
        """
        device_list = await self.async_get_inverter_data_retry(GE_API_EVC_DEVICES)
        devices = []
        if device_list is not None:
            for device in device_list:
                uuid = device.get("uuid", None)
                other_data = device.get("other_data", {})
                alias = device.get("alias", None)
                _LOGGER.info(
                    "Got EVC device uuid {} alias {}".format(
                        uuid, alias
                    )
                )
                devices.append(
                    {"uuid": uuid, "alias": alias}
                )
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
        return {}

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
                        _LOGGER.info("Got inverter serial {}".format(serial))
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
        self, endpoint, serial="", setting_id="", post=False, datain=None, uuid="", meter_ids="", start_time="", end_time="", command=""
    ):
        """
        Retry API call
        """
        for retry in range(RETRIES):
            data = await self.async_get_inverter_data(
                endpoint, serial, setting_id, post, datain, uuid, meter_ids, start_time=start_time, end_time=end_time, command=command
            )
            if data is not None:
                break
            await asyncio.sleep(1 * (retry + 1))
        if data is None:
            _LOGGER.error("Failed to get data from {}".format(endpoint))
        return data

    async def async_get_inverter_data(
        self, endpoint, serial="", setting_id="", post=False, datain=None, uuid="", meter_ids="", start_time="", end_time="", command=""
    ):
        """
        Basic API call to GE Cloud
        """
        url = GE_API_URL + endpoint.format(
            inverter_serial_number=serial, setting_id=setting_id, uuid=uuid, start_time=start_time, end_time=end_time, meter_ids=meter_ids, command=command
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
            if data is None:
                data = {}
            return data
        if response.status_code in [401, 403, 404, 422]:
            # Unauthorized
            return {}
        if response.status_code == 429:
            # Rate limiting so wait up to 30 seconds
            await asyncio.sleep(random.random() * 30)
        return None
