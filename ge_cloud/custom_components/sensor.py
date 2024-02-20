import voluptuous as vol
import logging

from homeassistant.util.dt import utcnow
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    entity_platform,
    issue_registry as ir,
    entity_registry as er,
)

from .const import (
    CONFIG_ACCOUNT_ID,
    CONFIG_KIND,
    CONFIG_KIND_ACCOUNT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Setup sensors based on our entry"""

    config = dict(entry.data)
    if config[CONFIG_KIND] == CONFIG_KIND_ACCOUNT:
        await async_setup_default_sensors(hass, config, async_add_entities)


async def async_setup_default_sensors(hass: HomeAssistant, config, async_add_entities):
    account_id = config[CONFIG_ACCOUNT_ID]
    _LOGGER.info(f"Setting up default sensors for account {account_id}")
