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
    DATA_SERIALS
)

from homeassistant.components.switch import (
    SwitchEntity,
    SwitchEntityDescription,
    SwitchDeviceClass
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


async def async_setup_default_switches(hass: HomeAssistant, config, serial, async_add_entities):
    """
    Setup default numbers
    """
    account_id = config[CONFIG_ACCOUNT_ID]
    coordinator = hass.data[DOMAIN][account_id][DATA_SERIALS][serial][DATA_ACCOUNT_COORDINATOR]
    _LOGGER.info(f"Setting up default switches for account {account_id}")

    cloud_switches = []
    if coordinator.type == 'inverter':
        for reg_id in coordinator.data['settings'].keys():
            reg_name = coordinator.data['settings'][reg_id]['name']
            ha_name = reg_name.lower().replace(' ', '_').replace('%', 'percent')
            value = coordinator.data['settings'][reg_id]['value']
            validation_rules = coordinator.data['settings'][reg_id]['validation_rules']
            device_class = None
            native_unit_of_measurement = ""
            is_switch = False
            for validation_rule in validation_rules:
                if validation_rule.startswith('boolean'):
                    is_switch = True
            if is_switch:
                _LOGGER.info(f"Setting up Switch {reg_id} ha_name {ha_name} reg_name {reg_name} value {value}")
                description = CloudSwitchEntityDescription(
                    key=ha_name,
                    name=reg_name,
                    unique_id=ha_name,
                    reg_number = reg_id,
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

        self._attr_name = f"GE Inverter {serial} {description.name}"
        self._attr_key = f"ge_inverter_{serial}_{description.key}"
        self._attr_device_class = description.device_class
        self._attr_unique_id = f"{coordinator.account_id}_{serial}_{description.unique_id}"
        self._attr_icon = description.icon
        self.reg_number = description.reg_number
        self.serial = serial

    @property
    def available(self) -> bool:
        return True

    @property
    def is_on(self) -> bool | None:
        """
        Return true if the switch is on
        """
        reg_number = self.entity_description.reg_number
        settings = self.coordinator.data.get('settings', {})
        value = settings.get(reg_number, {}).get('value', False)
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
            _LOGGER.info(f"Setting {key} number {reg_number} to {value}")
            result = await self.coordinator.api.async_write_inverter_setting(self.serial, reg_number, value)
            if result and ('value' in result):
                value = result['value']
                self.coordinator.data['settings'][reg_number]['value'] = value
            self.async_write_ha_state()