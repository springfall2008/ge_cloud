import voluptuous as vol
import logging

from homeassistant.util.dt import utcnow
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    entity_platform,
    issue_registry as ir,
    entity_registry as er,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONFIG_ACCOUNT_ID,
    CONFIG_KIND,
    CONFIG_KIND_ACCOUNT,
    DOMAIN,
    DATA_ACCOUNT_COORDINATOR,
    DATA_SERIALS,
    INTEGRATION_VERSION,
    EVC_COMMAND_NAMES
)

from homeassistant.components.switch import (
    SwitchEntity,
    SwitchEntityDescription,
    SwitchDeviceClass,
)
from .coordinator import CloudCoordinator
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any


@dataclass
class CloudSwitchEntityDescription(SwitchEntityDescription):
    """Provide a description of sensor"""

    # For backwards compat, allow description to override unique ID key to use
    unique_id: str | None = None
    reg_number: int | None = None


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Setup numbers based on our entry"""

    config = dict(entry.data)
    if config[CONFIG_KIND] == CONFIG_KIND_ACCOUNT:
        account_id = config[CONFIG_ACCOUNT_ID]
        for serial in hass.data[DOMAIN][account_id][DATA_SERIALS].keys():
            await async_setup_default_switches(hass, config, serial, async_add_entities)


async def async_setup_default_switches(
    hass: HomeAssistant, config, serial, async_add_entities
):
    """
    Setup default numbers
    """
    account_id = config[CONFIG_ACCOUNT_ID]
    coordinator = hass.data[DOMAIN][account_id][DATA_SERIALS][serial][
        DATA_ACCOUNT_COORDINATOR
    ]
    _LOGGER.info(
        f"Setting up default switches for account {account_id} type {coordinator.type} serial {serial}"
    )

    cloud_switches = []
    if coordinator.type == "inverter":
        for reg_id in coordinator.data["settings"].keys():
            reg_name = coordinator.data["settings"][reg_id]["name"]
            _LOGGER.info(f"Check for switch in {reg_id} {reg_name}")
            ha_name = reg_name.lower().replace(" ", "_").replace("%", "percent")
            value = coordinator.data["settings"][reg_id]["value"]
            validation_rules = coordinator.data["settings"][reg_id]["validation_rules"]
            device_class = None
            is_switch = False
            for validation_rule in validation_rules:
                if validation_rule.startswith("boolean"):
                    is_switch = True
                if validation_rule == "writeonly":
                    is_switch = True
            if is_switch:
                _LOGGER.info(
                    f"Setting up Switch {reg_id} ha_name {ha_name} reg_name {reg_name} value {value}"
                )
                description = CloudSwitchEntityDescription(
                    key=ha_name,
                    name=reg_name,
                    unique_id=ha_name,
                    reg_number=reg_id,
                    device_class=device_class,
                )
                cloud_switches.append(CloudSwitch(coordinator, description, serial))
    elif coordinator.type == "evc_device":
        for command in coordinator.data["commands"].keys():
            device_class = None
            command_data = coordinator.data["commands"][command]
            _LOGGER.info(f"Check for switch in {command} {command_data}")
            if isinstance(command_data, dict):
                value = command_data.get("value", None)
                if isinstance(value, bool):
                    description = CloudSwitchEntityDescription(
                        key=command,
                        name=EVC_COMMAND_NAMES.get(command, command),
                        unique_id=command,
                        reg_number=command,
                        device_class=device_class,
                    )
                    cloud_switches.append(CloudSwitch(coordinator, description, serial))
            elif isinstance(command_data, list) and len(command_data)==0:
                # Push button
                description = CloudSwitchEntityDescription(
                    key=command,
                    name=EVC_COMMAND_NAMES.get(command, command),
                    unique_id=command,
                    reg_number=command,
                    device_class=device_class,
                )
                cloud_switches.append(CloudSwitch(coordinator, description, serial))

    if cloud_switches:
        async_add_entities(cloud_switches)


class CloudSwitch(CoordinatorEntity[CloudCoordinator], SwitchEntity):
    """
    Switch class for GE Cloud
    """

    entity_description: str
    _attr_has_entity_name = True

    def __init__(self, coordinator, description, serial) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        device_name = coordinator.device_name

        if coordinator.type == "smart_device":
            self._attr_key = f"{description.key}"
            self._attr_name = f"{description.name}"
            self.device_name = f"GE Smart {device_name}"
            self.device_key = f"ge_smart_{serial}"
        elif coordinator.type == "evc_device":
            self._attr_key = f"{description.key}"
            self._attr_name = f"{description.name}"
            self.device_name = f"EVC {device_name}"
            self.device_key = f"ge_evc_{serial}"
        else:
            self._attr_key = f"{description.key}"
            self._attr_name = f"{description.name}"
            self.device_name = f"GE Inverter {device_name}"
            self.device_key = f"ge_inverter_{serial}"

        self._attr_device_class = description.device_class
        self._attr_unique_id = (
            f"{coordinator.account_id}_{serial}_{description.unique_id}"
        )
        self._attr_icon = description.icon
        self.reg_number = description.reg_number
        self.serial = serial

    @property
    def device_info(self):
        """
        Return device info
        """
        return {
            "identifiers": {(DOMAIN, self.device_key)},
            "name": self.device_name,
            "model": INTEGRATION_VERSION,
            "manufacturer": "GivEnergy",
        }

    @property
    def available(self) -> bool:
        """
        Return true if the switch is available
        """
        return not (self.is_on is None)

    @property
    def is_on(self) -> bool | None:
        """
        Return true if the switch is on
        """
        if self.coordinator.type == "evc_device":
            command = self.entity_description.reg_number
            command_data = self.coordinator.data["commands"].get(command, {})
            if isinstance(command_data, dict):
                return command_data.get("value", None)
            else:
                return False
        else:
            reg_number = self.entity_description.reg_number
            settings = self.coordinator.data.get("settings", {})
            value = settings.get(reg_number, {}).get("value", False)
        return value

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await self.async_set_toggle_value(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await self.async_set_toggle_value(False)

    async def async_set_toggle_value(self, value: bool) -> None:
        """Update the current value."""
        key = self.entity_description.key
        reg_number = self.entity_description.reg_number
        if value is not None:

            if self.coordinator.type == "evc_device":
                command_data = self.coordinator.data["commands"].get(reg_number, {})
                if isinstance(command_data, dict):
                    params = {'value' : value}
                else:
                    params = {}
                result = await self.coordinator.api.async_send_evc_command(self.serial, reg_number, params=params)
                _LOGGER.info(f"Setting {key} number {reg_number} setting {params} result {result}")
                if result:
                    self.coordinator.data["commands"][reg_number]["value"] = value
            else:
                validation_rules = self.coordinator.data["settings"][reg_number][
                    "validation_rules"
                ]
                if validation_rules:
                    for rule in validation_rules:
                        if rule.startswith("exact:"):
                            value = rule[6:]
                _LOGGER.info(f"Setting {key} number {reg_number} to {value}")
                result = await self.coordinator.api.async_write_inverter_setting(
                    self.serial, reg_number, value
                )
                if result and ("value" in result):
                    value = result["value"]
                    self.coordinator.data["settings"][reg_number]["value"] = value
            self.async_write_ha_state()
