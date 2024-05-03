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
    GE_REGISTER_BATTERY_CUTOFF_LIMIT,
    INTEGRATION_VERSION,
)
from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberDeviceClass,
)

from .coordinator import CloudCoordinator
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any


@dataclass
class CloudNumberEntityDescription(NumberEntityDescription):
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
            await async_setup_default_numbers(hass, config, serial, async_add_entities)


async def async_setup_default_numbers(
    hass: HomeAssistant, config, serial, async_add_entities
):
    """
    Setup default numbers
    """
    account_id = config[CONFIG_ACCOUNT_ID]
    coordinator = hass.data[DOMAIN][account_id][DATA_SERIALS][serial][
        DATA_ACCOUNT_COORDINATOR
    ]
    _LOGGER.info(f"Setting up default numbers for account {account_id} serial {serial}")

    cloud_numbers = []
    if coordinator.type == "inverter":
        for reg_id in coordinator.data["settings"].keys():
            reg_name = coordinator.data["settings"][reg_id]["name"]
            ha_name = reg_name.lower().replace(" ", "_").replace("%", "percent")
            value = coordinator.data["settings"][reg_id]["value"]
            validation_rules = coordinator.data["settings"][reg_id]["validation_rules"]
            device_class = None
            native_unit_of_measurement = ""
            if "%" in reg_name:
                device_class = NumberDeviceClass.BATTERY
                native_unit_of_measurement = "%"
            elif "_power_percent" in ha_name:
                device_class = NumberDeviceClass.POWER_FACTOR
                native_unit_of_measurement = "%"
            elif "_power" in ha_name:
                device_class = NumberDeviceClass.POWER
                native_unit_of_measurement = "W"
            is_number = False
            for validation_rule in validation_rules:
                if validation_rule.startswith("between:"):
                    is_number = True
                    range_min, range_max = validation_rule.split(":")[1].split(",")
            if is_number:
                _LOGGER.info(
                    f"Setting up number {reg_id} ha_name {ha_name} reg_name {reg_name} value {value}"
                )
                description = CloudNumberEntityDescription(
                    key=ha_name,
                    name=reg_name,
                    unique_id=ha_name,
                    native_unit_of_measurement=native_unit_of_measurement,
                    reg_number=reg_id,
                    device_class=device_class,
                    native_min_value=float(range_min),
                    native_max_value=float(range_max),
                )
                cloud_numbers.append(CloudNumber(coordinator, description, serial))
    if cloud_numbers:
        async_add_entities(cloud_numbers)


class CloudNumber(CoordinatorEntity[CloudCoordinator], NumberEntity):
    entity_description: str
    _attr_has_entity_name = True

    def __init__(self, coordinator, description, serial) -> None:
        super().__init__(coordinator)
        self.entity_description = description

        self._attr_name = f"{description.name}"
        self._attr_key = f"{description.key}"
        self.device_name = f"GE Inverter {serial}"
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
        Return true if the number is available
        """
        return not (self.native_value is None)

    @property
    def native_value(self) -> float | None:
        if not self.entity_description.key:
            return self.entity_description.name

        key = self.entity_description.key
        reg_number = self.entity_description.reg_number
        value = 0.0
        status = self.coordinator.data.get("status", {})
        meter = self.coordinator.data.get("meter", {})
        settings = self.coordinator.data.get("settings", {})
        value = settings.get(reg_number, {}).get("value", None)
        return value

    @property
    def native_unit_of_measurement(self) -> str | None:
        return self.entity_description.native_unit_of_measurement

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        key = self.entity_description.key
        reg_number = self.entity_description.reg_number
        if value is not None:
            _LOGGER.info(f"Setting {key} number {reg_number} to {value}")
            result = await self.coordinator.api.async_write_inverter_setting(
                self.serial, reg_number, value
            )
            if result and ("value" in result):
                value = result["value"]
                self.coordinator.data["settings"][reg_number]["value"] = value
            self.async_write_ha_state()
