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
    DATA_SERIALS,
    INTEGRATION_VERSION,
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
        device_class=SensorDeviceClass.BATTERY,
    ),
    CloudEntityDescription(
        key="battery_size",
        name="Battery Size",
        unique_id="battery_size",
        native_unit_of_measurement="kWh",
        icon="mdi:battery",
        device_class=SensorDeviceClass.ENERGY_STORAGE,
    ),
    CloudEntityDescription(
        key="battery_temperature",
        name="Battery Temperature",
        unique_id="battery_temperature",
        native_unit_of_measurement="°C",
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    CloudEntityDescription(
        key="battery_power",
        name="Battery Power",
        unique_id="battery_power",
        native_unit_of_measurement="W",
        icon="mdi:battery-charging-wireless-60",
        device_class=SensorDeviceClass.POWER,
    ),
    CloudEntityDescription(
        key="inverter_temperature",
        name="Inverter Temperature",
        unique_id="inverter_temperature",
        native_unit_of_measurement="°C",
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    CloudEntityDescription(
        key="inverter_power",
        name="Inverter Power",
        unique_id="inverter_power",
        native_unit_of_measurement="W",
        icon="mdi:generator-portable",
        device_class=SensorDeviceClass.POWER,
    ),
    CloudEntityDescription(
        key="grid_power",
        name="Grid Power",
        unique_id="grid_power",
        native_unit_of_measurement="W",
        icon="mdi:transmission-tower",
        device_class=SensorDeviceClass.POWER,
    ),
    CloudEntityDescription(
        key="grid_voltage",
        name="Grid Voltage",
        unique_id="grid_voltage",
        native_unit_of_measurement="V",
        icon="mdi:transmission-tower",
        device_class=SensorDeviceClass.VOLTAGE,
    ),
    CloudEntityDescription(
        key="solar_power",
        name="Solar Power",
        unique_id="solar_power",
        native_unit_of_measurement="W",
        icon="mdi:solar-power",
        device_class=SensorDeviceClass.POWER,
    ),
    CloudEntityDescription(
        key="solar_power_string1",
        name="Solar Power String 1",
        unique_id="solar_power_string1",
        native_unit_of_measurement="W",
        icon="mdi:solar-power",
        device_class=SensorDeviceClass.POWER,
    ),
    CloudEntityDescription(
        key="solar_power_string2",
        name="Solar Power String 2",
        unique_id="solar_power_string2",
        native_unit_of_measurement="W",
        icon="mdi:solar-power",
        device_class=SensorDeviceClass.POWER,
    ),
    CloudEntityDescription(
        key="solar_voltage_string1",
        name="Solar Voltage String 1",
        unique_id="solar_voltage_string1",
        native_unit_of_measurement="V",
        icon="mdi:transmission-tower",
        device_class=SensorDeviceClass.VOLTAGE,
    ),
    CloudEntityDescription(
        key="solar_voltage_string2",
        name="Solar Voltage String 2",
        unique_id="solar_voltage_string2",
        native_unit_of_measurement="V",
        icon="mdi:transmission-tower",
        device_class=SensorDeviceClass.VOLTAGE,
    ),
    CloudEntityDescription(
        key="solar_current_string1",
        name="Solar Current String 1",
        unique_id="solar_current_string1",
        native_unit_of_measurement="A",
        icon="mdi:transmission-tower",
        device_class=SensorDeviceClass.CURRENT,
    ),
    CloudEntityDescription(
        key="solar_current_string2",
        name="Solar Current String 2",
        unique_id="solar_current_string2",
        native_unit_of_measurement="A",
        icon="mdi:transmission-tower",
        device_class=SensorDeviceClass.CURRENT,
    ),
    CloudEntityDescription(
        key="consumption_power",
        name="Consumption Power",
        unique_id="consumption_power",
        native_unit_of_measurement="W",
        icon="mdi:home",
        device_class=SensorDeviceClass.POWER,
    ),
    CloudEntityDescription(
        key="solar_today",
        name="Solar Today",
        unique_id="solar_today",
        native_unit_of_measurement="kWh",
        icon="mdi:solar-panel-large",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    CloudEntityDescription(
        key="grid_import_today",
        name="Grid Import Today",
        unique_id="grid_import_today",
        native_unit_of_measurement="kWh",
        icon="mdi:transmission-tower-import",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    CloudEntityDescription(
        key="grid_export_today",
        name="Grid Export Today",
        unique_id="grid_export_today",
        native_unit_of_measurement="kWh",
        icon="mdi:transmission-tower-export",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    CloudEntityDescription(
        key="consumption_today",
        name="Consumption Today",
        unique_id="consumption_today",
        native_unit_of_measurement="kWh",
        icon="mdi:home",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    CloudEntityDescription(
        key="battery_charge_today",
        name="Battery Charge total Today",
        unique_id="battery_charge_today",
        native_unit_of_measurement="kWh",
        icon="mdi:transmission-tower-import",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    CloudEntityDescription(
        key="battery_discharge_today",
        name="Battery Discharge Today",
        unique_id="battery_discharge_today",
        native_unit_of_measurement="kWh",
        icon="mdi:transmission-tower-export",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    CloudEntityDescription(
        key="solar_total",
        name="Solar Total",
        unique_id="solar_total",
        native_unit_of_measurement="kWh",
        icon="mdi:solar-panel-large",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    CloudEntityDescription(
        key="grid_import_total",
        name="Grid Import Total",
        unique_id="grid_import_total",
        native_unit_of_measurement="kWh",
        icon="mdi:transmission-tower-import",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    CloudEntityDescription(
        key="grid_export_total",
        name="Grid Export Total",
        unique_id="grid_export_total",
        native_unit_of_measurement="kWh",
        icon="mdi:transmission-tower-export",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    CloudEntityDescription(
        key="consumption_total",
        name="Consumption Total",
        unique_id="consumption_total",
        native_unit_of_measurement="kWh",
        icon="mdi:home",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    CloudEntityDescription(
        key="battery_charge_total",
        name="Battery Charge total Total",
        unique_id="battery_charge_total",
        native_unit_of_measurement="kWh",
        icon="mdi:transmission-tower-import",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    CloudEntityDescription(
        key="battery_discharge_total",
        name="Battery Discharge Total",
        unique_id="battery_discharge_total",
        native_unit_of_measurement="kWh",
        icon="mdi:transmission-tower-export",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    CloudEntityDescription(
        key="time",
        name="Inverter time",
        unique_id="time",
        icon="mdi:timer-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
)
SENSORS_SMART_DEVICE = (
    CloudEntityDescription(
        key="power",
        name="Power",
        unique_id="power",
        native_unit_of_measurement="W",
        icon="mdi:information",
        device_class=SensorDeviceClass.POWER,
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Setup sensors based on our entry"""

    config = dict(entry.data)
    if config[CONFIG_KIND] == CONFIG_KIND_ACCOUNT:
        account_id = config[CONFIG_ACCOUNT_ID]
        for serial in hass.data[DOMAIN][account_id][DATA_SERIALS].keys():
            await async_setup_default_sensors(hass, config, serial, async_add_entities)


async def async_setup_default_sensors(
    hass: HomeAssistant, config, serial, async_add_entities
):
    """
    Setup default sensors
    """
    account_id = config[CONFIG_ACCOUNT_ID]
    coordinator = hass.data[DOMAIN][account_id][DATA_SERIALS][serial][
        DATA_ACCOUNT_COORDINATOR
    ]
    if coordinator.type == "smart_device":
        sensors = SENSORS_SMART_DEVICE
    else:
        sensors = SENSORS_INVERTER
    _LOGGER.info(
        f"Setting up default sensors for account {account_id} type {coordinator.type} serial {serial}"
    )
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
            self._attr_key = f"{description.key}"
            self._attr_name = f"{description.name}"
            self.device_name = f"GE Smart {device_name}"
            self.device_key = f"ge_smart_{serial}"
        else:
            self._attr_key = f"{description.key}"
            self._attr_name = f"{description.name}"
            self.device_name = f"GE Inverter {device_name}"
            self.device_key = f"ge_inverter_{serial}"
        self._attr_state_class = description.state_class
        self._attr_device_class = description.device_class
        self._attr_unique_id = (
            f"{coordinator.account_id}_{serial}_{description.unique_id}"
        )
        self._attr_icon = description.icon
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
        Return if entity is available
        """
        return not (self.native_value is None)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if self.coordinator.type == "smart_device":
            smart_device = self.coordinator.data.get("smart_device", {})
            return {
                "local_key": smart_device.get("local_key"),
                "uuid": smart_device.get("uuid"),
                "asset_id": smart_device.get("asset_id"),
                "device_id": smart_device.get("hardware_id"),
            }
        return None

    @property
    def native_value(self) -> float | datetime | None:
        if not self.entity_description.key:
            return self.entity_description.name

        key = self.entity_description.key
        value = None

        if self.coordinator.type == "smart_device":
            smart_device = self.coordinator.data.get("smart_device", {})
            smart_point = self.coordinator.data.get("point", {})
            if key == "power":
                value = smart_point.get("power", None)
        else:
            status = self.coordinator.data.get("status", {})
            meter = self.coordinator.data.get("meter", {})
            info = self.coordinator.data.get("info", {})
            if key == "battery_soc":
                value = status.get("battery", {}).get("percent", None)
            elif key == "time":
                value = status.get("time", None)
                if value:
                    value = value.replace("Z", "+00:00")
                    try:
                        value = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z")
                    except (ValueError, TypeError):
                        value = None
            elif key == "battery_size":
                cap = (
                    info.get("info", {})
                    .get("battery", {})
                    .get("nominal_capacity", None)
                )
                volt = (
                    info.get("info", {}).get("battery", {}).get("nominal_voltage", None)
                )
                if cap and volt:
                    value = round(cap * volt / 1000.0, 2)
            elif key == "battery_temperature":
                value = status.get("battery", {}).get("temperature", None)
            elif key == "battery_power":
                value = status.get("battery", {}).get("power", None)
            elif key == "inverter_temperature":
                value = status.get("inverter", {}).get("temperature", None)
            elif key == "inverter_power":
                value = status.get("inverter", {}).get("power", None)
            elif key == "grid_voltage":
                value = status.get("grid", {}).get("voltage", None)
            elif key == "grid_power":
                value = status.get("grid", {}).get("power", None)
            elif key == "solar_power":
                value = status.get("solar", {}).get("power", None)
            elif key == "solar_power_string1":
                value = None
                array = status.get("solar", {}).get("arrays", [])
                if len(array) > 0:
                    value = array[0].get("power", None)
            elif key == "solar_power_string2":
                value = None
                array = status.get("solar", {}).get("arrays", [])
                if len(array) > 1:
                    value = array[1].get("power", None)
            elif key == "solar_current_string1":
                value = None
                array = status.get("solar", {}).get("arrays", [])
                if len(array) > 0:
                    value = array[0].get("current", None)
            elif key == "solar_current_string2":
                value = None
                array = status.get("solar", {}).get("arrays", [])
                if len(array) > 1:
                    value = array[1].get("current", None)
            elif key == "solar_voltage_string1":
                value = None
                array = status.get("solar", {}).get("arrays", [])
                if len(array) > 0:
                    value = array[0].get("voltage", None)
            elif key == "solar_voltage_string2":
                value = None
                array = status.get("solar", {}).get("arrays", [])
                if len(array) > 1:
                    value = array[1].get("voltage", None)
            elif key == "consumption_power":
                value = status.get("consumption", None)
            elif key == "solar_today":
                value = meter.get("today", {}).get("solar", None)
            elif key == "grid_import_today":
                value = meter.get("today", {}).get("grid", {}).get("import", None)
            elif key == "grid_export_today":
                value = meter.get("today", {}).get("grid", {}).get("export", None)
            elif key == "consumption_today":
                value = meter.get("today", {}).get("consumption", None)
            elif key == "battery_charge_today":
                value = meter.get("today", {}).get("battery", {}).get("charge", None)
            elif key == "battery_discharge_today":
                value = meter.get("today", {}).get("battery", {}).get("discharge", None)
            elif key == "solar_total":
                value = meter.get("total", {}).get("solar", None)
            elif key == "grid_import_total":
                value = meter.get("total", {}).get("grid", {}).get("import", None)
            elif key == "grid_export_total":
                value = meter.get("total", {}).get("grid", {}).get("export", None)
            elif key == "consumption_total":
                value = meter.get("total", {}).get("consumption", None)
            elif key == "battery_charge_total":
                value = meter.get("total", {}).get("battery", {}).get("charge", None)
            elif key == "battery_discharge_total":
                value = meter.get("total", {}).get("battery", {}).get("discharge", None)
        return value

    @property
    def native_unit_of_measurement(self) -> str | None:
        return self.entity_description.native_unit_of_measurement
