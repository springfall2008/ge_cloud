import voluptuous as vol
import logging
import pytz

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
SENSORS_INVERTER = (
    CloudEntityDescription(
        key="battery_soc",
        name="Battery SOC",
        unique_id="battery_soc",
        native_unit_of_measurement="%",
        icon="mdi:battery",
        state_class=SensorStateClass.MEASUREMENT
    ),
    CloudEntityDescription(
        key="battery_size",
        name="Battery Size",
        unique_id="battery_size",
        native_unit_of_measurement="kWh",
        icon="mdi:battery",
        state_class=SensorStateClass.MEASUREMENT
    ),
    CloudEntityDescription(
        key="battery_temperature",
        name="Battery Temperature",
        unique_id="battery_temperature",
        native_unit_of_measurement="c",
        icon="mdi:thermometer",
        state_class=SensorStateClass.MEASUREMENT
    ),
    CloudEntityDescription(
        key="battery_power",
        name="Battery Power",
        unique_id="battery_power",
        native_unit_of_measurement="w",
        icon="mdi:battery-charging-wireless-60",
        state_class=SensorStateClass.MEASUREMENT
    ),
    CloudEntityDescription(
        key="inverter_temperature",
        name="Inverter Temperature",
        unique_id="inverter_temperature",
        native_unit_of_measurement="c",
        icon="mdi:thermometer",
        state_class=SensorStateClass.MEASUREMENT
    ),
    CloudEntityDescription(
        key="inverter_power",
        name="Inverter Power",
        unique_id="inverter_power",
        native_unit_of_measurement="w",
        icon="mdi:generator-portable",
        state_class=SensorStateClass.MEASUREMENT
    ),
    CloudEntityDescription(
        key="grid_power",
        name="Grid Power",
        unique_id="grid_power",
        native_unit_of_measurement="w",
        icon="mdi:transmission-tower",
        state_class=SensorStateClass.MEASUREMENT
    ),
    CloudEntityDescription(
        key="grid_voltage",
        name="Grid Voltage",
        unique_id="grid_voltage",
        native_unit_of_measurement="v",
        icon="mdi:transmission-tower",
        state_class=SensorStateClass.MEASUREMENT
    ),
    CloudEntityDescription(
        key="solar_power",
        name="Solar Power",
        unique_id="solar_power",
        native_unit_of_measurement="w",
        icon="mdi:solar-power",
        state_class=SensorStateClass.MEASUREMENT
    ),
    CloudEntityDescription(
        key="consumption_power",
        name="Consumption Power",
        unique_id="consumption_power",
        native_unit_of_measurement="w",
        icon="mdi:home",
        state_class=SensorStateClass.MEASUREMENT
    ),
    CloudEntityDescription(
        key="solar_today",
        name="Solar Today",
        unique_id="solar_today",
        native_unit_of_measurement="kWh",
        icon="mdi:solar-panel-large",
        state_class=SensorStateClass.MEASUREMENT
    ),
    CloudEntityDescription(
        key="grid_import_today",
        name="Grid Import Today",
        unique_id="grid_import_today",
        native_unit_of_measurement="kWh",
        icon="mdi:transmission-tower-import",
        state_class=SensorStateClass.MEASUREMENT
    ),
    CloudEntityDescription(
        key="grid_export_today",
        name="Grid Export Today",
        unique_id="grid_export_today",
        native_unit_of_measurement="kWh",
        icon="mdi:transmission-tower-export",
        state_class=SensorStateClass.MEASUREMENT
    ),
    CloudEntityDescription(
        key="consumption_today",
        name="Consumption Today",
        unique_id="consumption_today",
        native_unit_of_measurement="kWh",
        icon="mdi:home",
        state_class=SensorStateClass.MEASUREMENT
    ),
    CloudEntityDescription(
        key="time",
        name="Inverter time",
        unique_id="time",
        icon="mdi:timer-outline",
        device_class=SensorDeviceClass.TIMESTAMP
    )
)
SENSORS_SMART_DEVICE = (
    CloudEntityDescription(
        key="power",
        name="Power",
        unique_id="power",
        native_unit_of_measurement="w",
        icon="mdi:information",
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
    account_id = config[CONFIG_ACCOUNT_ID]
    coordinator = hass.data[DOMAIN][account_id][DATA_SERIALS][serial][DATA_ACCOUNT_COORDINATOR]
    if coordinator.type == "smart_device":
        sensors = SENSORS_SMART_DEVICE
    else:
        sensors = SENSORS_INVERTER
    _LOGGER.info(f"Setting up default sensors for account {account_id} type {coordinator.type} serial {serial}")
    async_add_entities(
        CloudSensor(coordinator, description, serial) for description in sensors
    )

class CloudSensor(CoordinatorEntity[CloudCoordinator], SensorEntity):
    entity_description: str
    _attr_has_entity_name = True

    def __init__(self, coordinator, description, serial) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        device_name = coordinator.device_name

        if coordinator.type == "smart_device":
            self._attr_key = f"ge_smart_{serial}_{description.key}"
            self._attr_name = f"GE Smart {device_name} {description.name}"
        else:
            self._attr_key = f"ge_inverter_{serial}_{description.key}"
            self._attr_name = f"GE Inverter {device_name} {description.name}"
        self._attr_state_class = description.state_class
        self._attr_device_class = description.device_class
        self._attr_unique_id = f"{coordinator.account_id}_{serial}_{description.unique_id}"
        self._attr_icon = description.icon
        self.serial = serial

    @property
    def available(self) -> bool:
        return True

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if self.coordinator.type == "smart_device":
            smart_device = self.coordinator.data.get('smart_device', {})
            return {"local_key" : smart_device.get('local_key'),
                    "uuid" : smart_device.get('uuid'),
                    "asset_id" : smart_device.get('asset_id'),
                    "device_id" : smart_device.get('hardware_id'),
                    }
        return None

    @property
    def native_value(self) -> float | datetime | None:
        if not self.entity_description.key:
            return self.entity_description.name

        key = self.entity_description.key
        value = 0.0

        if self.coordinator.type == "smart_device":
            smart_device = self.coordinator.data.get('smart_device', {})
            smart_point = self.coordinator.data.get('point', {})
            if key == 'power':
                value = smart_point.get('power', 0)
        else:
            status = self.coordinator.data.get('status', {})
            meter = self.coordinator.data.get('meter', {})
            info  = self.coordinator.data.get('info', {})
            if key == 'battery_soc':
                value = status.get('battery', {}).get('percent', 0.0)
            elif key == 'time':
                value = status.get('time', None)
                if value:
                    try:
                        tz = pytz.timezone("Europe/London")
                        value = tz.localize(datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ"))
                    except (ValueError, TypeError):
                        value = None
            elif key == 'battery_size':
                cap = info.get('info', {}).get('battery', {}).get('nominal_capacity', 0.0)
                volt = info.get('info', {}).get('battery', {}).get('nominal_voltage', 0.0)
                value = round(cap * volt / 1000.0, 2)
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
            elif key == 'solar_today':
                value = meter.get('today', {}).get('solar', 0.0)
            elif key == 'grid_import_today':
                value = meter.get('today', {}).get('grid', 0.0).get('import', 0.0)
            elif key == 'grid_export_today':
                value = meter.get('today', {}).get('grid', 0.0).get('export', 0.0)
            elif key == 'consumption_today':
                value = meter.get('today', {}).get('consumption', 0.0)
        return value

    @property
    def native_unit_of_measurement(self) -> str | None:
        return self.entity_description.native_unit_of_measurement