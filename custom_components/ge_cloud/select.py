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
)

from homeassistant.components.select import (
    SelectEntity,
    SelectEntityDescription,
)
from .coordinator import CloudCoordinator
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

BASE_TIME = datetime.strptime("00:00", "%H:%M")
OPTIONS_TIME = [
    ((BASE_TIME + timedelta(seconds=minute * 60)).strftime("%H:%M"))
    for minute in range(0, 24 * 60, 1)
]


@dataclass
class CloudSelectEntityDescription(SelectEntityDescription):
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
            await async_setup_default_selects(hass, config, serial, async_add_entities)


async def async_setup_default_selects(
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
        f"Setting up default selects for account {account_id} serial {serial} type {coordinator.type}"
    )
    cloud_selects = []
    if coordinator.type == "inverter":
        for reg_id in coordinator.data["settings"].keys():
            reg_name = coordinator.data["settings"][reg_id]["name"]
            ha_name = reg_name.lower().replace(" ", "_").replace("%", "percent")
            value = coordinator.data["settings"][reg_id]["value"]
            validation_rules = coordinator.data["settings"][reg_id]["validation_rules"]
            device_class = None
            native_unit_of_measurement = ""
            is_select = False
            for validation_rule in validation_rules:
                if validation_rule.startswith("date_format:H:i"):
                    is_select = True
            if is_select:
                _LOGGER.info(
                    f"Setting up Select {reg_id} ha_name {ha_name} reg_name {reg_name} value {value}"
                )
                description = CloudSelectEntityDescription(
                    key=ha_name,
                    name=reg_name,
                    unique_id=ha_name,
                    reg_number=reg_id,
                    device_class=device_class,
                )
                cloud_selects.append(CloudSelect(coordinator, description, serial))
    if cloud_selects:
        async_add_entities(cloud_selects)


class CloudSelect(CoordinatorEntity[CloudCoordinator], SelectEntity):
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
        self._attr_unique_id = (
            f"{coordinator.account_id}_{serial}_{description.unique_id}"
        )
        self._attr_icon = description.icon
        self._attr_options = OPTIONS_TIME
        self.reg_number = description.reg_number
        self.serial = serial

    @property
    def available(self) -> bool:
        return True

    @property
    def current_option(self) -> str:
        option = self.coordinator.data["settings"][self.reg_number]["value"]
        _LOGGER.info(
            f"Getting current option for {self.entity_description.key} number {self.reg_number} returns {option}"
        )
        return option

    async def async_select_option(self, option: str) -> None:
        """Update the current value."""
        key = self.entity_description.key
        reg_number = self.entity_description.reg_number
        if option is not None:
            _LOGGER.info(f"Setting {key} number {reg_number} to {option}")
            result = await self.coordinator.api.async_write_inverter_setting(
                self.serial, reg_number, option
            )
            if result and ("value" in result):
                option = result["value"]
                self.coordinator.data["settings"][reg_number]["value"] = option
            self.async_write_ha_state()
