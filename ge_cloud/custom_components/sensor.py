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
        unique_id="battery_soc2",
        native_unit_of_measurement="%",
        icon="mdi:battery",
        state_class=SensorStateClass.MEASUREMENT
    ),
    CloudEntityDescription(
        key="battery_temperature",
        name="Battery Temperature",
        unique_id="battery_temperature2",
        native_unit_of_measurement="c",
        icon="mdi:battery",
        state_class=SensorStateClass.MEASUREMENT
    ),
    CloudEntityDescription(
        key="battery_power",
        name="Battery Power",
        unique_id="battery_power",
        native_unit_of_measurement="w",
        icon="mdi:battery",
        state_class=SensorStateClass.MEASUREMENT
    ),
    CloudEntityDescription(
        key="inverter_temperature",
        name="Inverter Temperature",
        unique_id="inverter_temperature",
        native_unit_of_measurement="c",
        icon="mdi:battery",
        state_class=SensorStateClass.MEASUREMENT
    ),
    CloudEntityDescription(
        key="inverter_power",
        name="Inverter Power",
        unique_id="inverter_power",
        native_unit_of_measurement="w",
        icon="mdi:battery",
        state_class=SensorStateClass.MEASUREMENT
    ),
    CloudEntityDescription(
        key="grid_power",
        name="Grid Power",
        unique_id="grid_power",
        native_unit_of_measurement="w",
        icon="mdi:battery",
        state_class=SensorStateClass.MEASUREMENT
    ),
    CloudEntityDescription(
        key="grid_voltage",
        name="Grid Voltage",
        unique_id="grid_voltage",
        native_unit_of_measurement="v",
        icon="mdi:battery",
        state_class=SensorStateClass.MEASUREMENT
    ),
    CloudEntityDescription(
        key="solar_power",
        name="Solar Power",
        unique_id="solar_power",
        native_unit_of_measurement="w",
        icon="mdi:battery",
        state_class=SensorStateClass.MEASUREMENT
    ),
    CloudEntityDescription(
        key="consumption_power",
        name="Consumption Power",
        unique_id="consumption_power",
        native_unit_of_measurement="w",
        icon="mdi:battery",
        state_class=SensorStateClass.MEASUREMENT
    ),
)

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Setup sensors based on our entry"""

    config = dict(entry.data)
    if config[CONFIG_KIND] == CONFIG_KIND_ACCOUNT:
        account_id = config[CONFIG_ACCOUNT_ID]
        for serial in hass.data[DOMAIN][account_id][DATA_SERIALS].keys():
            await async_setup_default_sensors(hass, config, serial, async_add_entities)


async def async_setup_default_sensors(hass: HomeAssistant, config, serial, async_add_entities):
    """
    Setup default sensors
    """
    sensors = SENSORS
    account_id = config[CONFIG_ACCOUNT_ID]
    coordinator = hass.data[DOMAIN][account_id][DATA_SERIALS][serial][DATA_ACCOUNT_COORDINATOR]
    _LOGGER.info(f"Setting up default sensors for account {account_id}")
    async_add_entities(
        CloudSensor(coordinator, description, serial) for description in sensors
    )

class CloudSensor(CoordinatorEntity[CloudCoordinator], SensorEntity):
    entity_description: str
    _attr_has_entity_name = True

    def __init__(self, coordinator, description, serial) -> None:
        super().__init__(coordinator)
        self.entity_description = description

        self._attr_name = f"{serial} {description.name}"
        self._attr_key = f"{serial}_{description.key}"
        self._attr_state_class = description.state_class
        self._attr_device_class = description.device_class
        self._attr_unique_id = f"{coordinator.account_id}_{serial}_{description.unique_id}"
        self._attr_icon = description.icon
        self.serial = serial

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
        elif key == 'battery_power':
            value = status.get('battery', {}).get('power', 0.0)
        elif key == 'inverter_temperature':
            value = status.get('inverter', {}).get('temperature', 0.0)
        elif key == 'inverter_power':
            value = status.get('inverter', {}).get('power', 0.0)
        elif key == 'grid_voltage':
            value = status.get('grid', {}).get('voltage', 0.0)
        elif key == 'grid_power':
            value = status.get('grid', {}).get('power', 0.0)
        elif key == 'solar_power':
            value = status.get('solar', {}).get('power', 0.0)
        elif key == 'consumption_power':
            value = status.get('consumption', 0.0)
        return value

    @property
    def native_unit_of_measurement(self) -> str | None:
        return self.entity_description.native_unit_of_measurement