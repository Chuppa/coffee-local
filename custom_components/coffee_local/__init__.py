"""Coffee Local integration: HA owns HTTP polling; the bridge owns the machine."""
from datetime import timedelta
import logging

from homeassistant.const import Platform
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BridgeClient, BridgeAuthError, BridgeError
from .const import DOMAIN, CONF_URL, CONF_TOKEN

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.SWITCH, Platform.BUTTON]

class CoffeeCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        super().__init__(hass, logging.getLogger(__name__), name=DOMAIN,
                         config_entry=entry, update_interval=timedelta(seconds=5))
        self.client = BridgeClient(async_get_clientsession(hass), entry.data[CONF_URL], entry.data[CONF_TOKEN])
        self.device_id = entry.unique_id

    async def _async_update_data(self):
        try:
            data = await self.client.status()
            if data['device']['id'] != self.device_id:
                raise BridgeError('Bridge device changed; configure the new machine separately')
            return data
        except BridgeAuthError as exc:
            raise ConfigEntryAuthFailed(str(exc)) from exc
        except BridgeError as exc:
            raise UpdateFailed(str(exc)) from exc

async def async_setup_entry(hass, entry):
    coordinator = CoffeeCoordinator(hass, entry)
    # Server reachable but machine offline is a valid setup; entities recover on polling.
    # Bridge offline uses HA's automatic ConfigEntryNotReady retry.
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass, entry):
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
