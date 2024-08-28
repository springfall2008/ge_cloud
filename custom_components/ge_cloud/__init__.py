import logging
from datetime import timedelta

from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.components.recorder import get_instance
from homeassistant.util.dt import utcnow
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .api import GECloudApiClient
from .coordinator import async_setup_cloud_coordinator

from .const import (
    CONFIG_ACCOUNT_ID,
    CONFIG_MAIN_API_KEY,
    DOMAIN,
    DATA_CLIENT,
    CONFIG_KIND_ACCOUNT,
    CONFIG_KIND,
    DATA_ACCOUNT,
    DATA_SERIALS,
    CONFIG_INVERTER_ENABLE,
    CONFIG_SMART_DEVICE_ENABLE,
    CONFIG_EVC_ENABLE,
    CONFIG_POLL_INVERTER,
)

ACCOUNT_PLATFORMS = ["sensor", "number", "switch", "select"]
_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config):
    """
    This is called by Home Assistant when setting up the component.
    """
    _LOGGER.info("Setting up ge_cloud config {}".format(config))

    # Return boolean to indicate that initialization was successful.
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """This is called from the config flow."""
    _LOGGER.info("Setting up entry {}".format(entry))
    hass.data.setdefault(DOMAIN, {})

    config = dict(entry.data)

    account_id = config[CONFIG_ACCOUNT_ID]
    api_key = config[CONFIG_MAIN_API_KEY]
    _LOGGER.info("Setting up entry for account {}".format(account_id))
    hass.data[DOMAIN].setdefault(account_id, {})
    if config[CONFIG_KIND] == CONFIG_KIND_ACCOUNT:
        await async_setup_dependencies(hass, config)
        await hass.config_entries.async_forward_entry_setups(entry, ACCOUNT_PLATFORMS)
    return True


async def async_setup_dependencies(hass: HomeAssistant, config):
    """Setup the coordinator and api client which will be shared by various entities"""
    account_id = config[CONFIG_ACCOUNT_ID]
    api_key = config[CONFIG_MAIN_API_KEY]
    inverter_enable = config.get(CONFIG_INVERTER_ENABLE, True)
    smart_device_enable = config.get(CONFIG_SMART_DEVICE_ENABLE)
    evc_enable = config.get(CONFIG_EVC_ENABLE)
    poll_inverter = config.get(CONFIG_POLL_INVERTER)

    _LOGGER.info("Create API Client for account {}".format(account_id))
    client = GECloudApiClient(account_id, api_key)
    hass.data[DOMAIN][account_id][DATA_CLIENT] = client
    hass.data[DOMAIN][account_id][DATA_SERIALS] = {}

    if inverter_enable:
        serials = await client.async_get_devices()
        _LOGGER.info("Got inverter serials {}".format(serials))
        for serial in serials:
            hass.data[DOMAIN][account_id][DATA_SERIALS][serial] = {}
            _LOGGER.info(
                "Create Inverter Cloud coordinator for account {} serial {}".format(
                    account_id, serial
                )
            )
            await async_setup_cloud_coordinator(hass, account_id, serial, type="inverter", polling=poll_inverter)

    if smart_device_enable:
        smart_devices = await client.async_get_smart_devices()
        _LOGGER.info("Got smart devices {}".format(smart_devices))
        for device in smart_devices:
            uuid = device.get("uuid", None)
            if uuid:
                hass.data[DOMAIN][account_id][DATA_SERIALS][uuid] = {}
                _LOGGER.info(
                    "Create Smart Device Cloud coordinator for account {} UUID {}".format(
                        account_id, uuid
                    )
                )
                await async_setup_cloud_coordinator(
                    hass,
                    account_id,
                    uuid,
                    type="smart_device",
                    device_name=device.get("alias", None),
                )

    if evc_enable:
        evc_devices = await client.async_get_evc_devices()
        _LOGGER.info("Got EVC devices {}".format(evc_devices))
        for device in evc_devices:
            uuid = device.get("uuid", None)
            if uuid:
                hass.data[DOMAIN][account_id][DATA_SERIALS][uuid] = {}
                _LOGGER.info(
                    "Create EVC Cloud coordinator for account {} UUID {}".format(
                        account_id, uuid
                    )
                )
                await async_setup_cloud_coordinator(
                    hass,
                    account_id,
                    uuid,
                    type="evc_device",
                    device_name=device.get("alias", None),
                )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = False
    if CONFIG_MAIN_API_KEY in entry.data:
        unload_ok = await hass.config_entries.async_unload_platforms(
            entry, ACCOUNT_PLATFORMS
        )

    return unload_ok
