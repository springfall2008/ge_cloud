import logging
from datetime import timedelta

from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.components.recorder import get_instance
from homeassistant.util.dt import utcnow
from homeassistant.const import EVENT_HOMEASSISTANT_STOP


from .const import CONFIG_ACCOUNT_ID, CONFIG_MAIN_API_KEY, DOMAIN

ACCOUNT_PLATFORMS = [
    "sensor",
]
_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    """
    This is called by Home Assistant when setting up the component.
    """
    hass.states.async_set("ge_cloud.status", "Setup")
    _LOGGER.info("Setting up ge_cloud")

    # Return boolean to indicate that initialization was successful.
    return True


async def async_setup_entry(hass, entry):
    """This is called from the config flow."""
    hass.data.setdefault(DOMAIN, {})

    config = dict(entry.data)

    if entry.options:
        config.update(entry.options)

    account_id = config[CONFIG_ACCOUNT_ID]
    hass.data[DOMAIN].setdefault(account_id, {})

    await async_setup_dependencies(hass, config)
    await hass.config_entries.async_forward_entry_setups(entry, ACCOUNT_PLATFORMS)
    return True


async def async_setup_dependencies(hass, config):
    """Setup the coordinator and api client which will be shared by various entities"""
    account_id = config[CONFIG_ACCOUNT_ID]


async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    unload_ok = False
    if CONFIG_MAIN_API_KEY in entry.data:
        unload_ok = await hass.config_entries.async_unload_platforms(
            entry, ACCOUNT_PLATFORMS
        )

    return unload_ok
