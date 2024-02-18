DOMAIN = "ge_cloud"


async def async_setup(hass, config):
    hass.states.async_set("ge_cloud.hello", "World")

    # Return boolean to indicate that initialization was successful.
    return True
