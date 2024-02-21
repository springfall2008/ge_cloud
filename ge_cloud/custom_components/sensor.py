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
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from .coordinator import CloudCoordinator
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

@dataclass
class CloudEntityDescription(SensorEntityDescription):
    """Provide a description of sensor"""

    # For backwards compat, allow description to override unique ID key to use
    unique_id: str | None = None

_LOGGER = logging.getLogger(__name__)
SENSORS = (
    CloudEntityDescription(
        key="battery_soc",
        name="Battery SOC",
        unique_id="battery_soc",
        native_unit_of_measurement="%",
        icon="mdi:battery",
        state_class=SensorStateClass.MEASUREMENT
    ),
    CloudEntityDescription(
        key="battery_temperature",
        name="Battery Temperature",
        unique_id="battery_temperature",
        native_unit_of_measurement="c",
        icon="mdi:battery",
        state_class=SensorStateClass.MEASUREMENT
    ),
)

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Setup sensors based on our entry"""

    config = dict(entry.data)
    if config[CONFIG_KIND] == CONFIG_KIND_ACCOUNT:
        await async_setup_default_sensors(hass, config, async_add_entities)


async def async_setup_default_sensors(hass: HomeAssistant, config, async_add_entities):
    """
    Setup default sensors
    """
    sensors = SENSORS
    account_id = config[CONFIG_ACCOUNT_ID]
    coordinator = hass.data[DOMAIN][account_id][DATA_ACCOUNT_COORDINATOR]
    _LOGGER.info(f"Setting up default sensors for account {account_id}")
    async_add_entities(
        CloudSensor(coordinator, description) for description in sensors
    )

class CloudSensor(CoordinatorEntity[CloudCoordinator], SensorEntity):
    entity_description: str
    _attr_has_entity_name = True

    def __init__(self, coordinator, description) -> None:
        super().__init__(coordinator)
        self.entity_description = description

        self._attr_state_class = description.state_class
        self._attr_device_class = description.device_class
        self._attr_unique_id = f"{coordinator.account_id}_{description.unique_id}"
        self._attr_icon = description.icon

    @property
    def available(self) -> bool:
        return True

    @property
    def native_value(self) -> float | datetime | None:
        if not self.entity_description.key:
            return self.entity_description.name

        key = self.entity_description.key
        value = 0.0
        status = self.coordinator.data.get('status', {})
        if key == 'battery_soc':
            value = status.get('battery', {}).get('percent', 0.0)
        elif key == 'battery_temperature':
            value = status.get('battery', {}).get('temperature', 0.0)
        return value

    @property
    def native_unit_of_measurement(self) -> str | None:
        return self.entity_description.native_unit_of_measurement