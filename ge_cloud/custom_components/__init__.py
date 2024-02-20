import logging
from datetime import timedelta

from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.components.recorder import get_instance
from homeassistant.util.dt import utcnow
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONFIG_ACCOUNT_ID, CONFIG_MAIN_API_KEY, DOMAIN, DATA_CLIENT, CONFIG_KIND_ACCOUNT, CONFIG_KIND

ACCOUNT_PLATFORMS = [
    "sensor",
]
_LOGGER = logging.getLogger(__name__)

from .coordinator import GECloudCoordinator

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
    _LOGGER.info("Setting up dependencies for account {} api_key {}".format(account_id, api_key))
    coodinator = GECloudCoordinator(hass, config, account_id, api_key)
    hass.data[DOMAIN][DATA_CLIENT] = coodinator


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = False
    if CONFIG_MAIN_API_KEY in entry.data:
        unload_ok = await hass.config_entries.async_unload_platforms(
            entry, ACCOUNT_PLATFORMS
        )

    return unload_ok
