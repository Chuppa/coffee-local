"""Coffee Local integration: HA owns HTTP polling; the bridge owns the machine."""
from datetime import timedelta
import logging

from homeassistant.const import Platform
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BridgeClient, BridgeAuthError, BridgeError
from .const import DOMAIN, CONF_URL, CONF_TOKEN

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.SWITCH]

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
    # Remove retired entities from earlier releases so updates do not leave a
    # device page full of unavailable drink buttons and unmapped protocol fields.
    registry = er.async_get(hass)
    retired = {entry.unique_id + '_action_name', entry.unique_id + '_is_idle'}
    for entity in er.async_entries_for_config_entry(registry, entry.entry_id):
        if entity.domain == 'button' or entity.unique_id in retired:
            registry.async_remove(entity.entity_id)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass, entry):
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
