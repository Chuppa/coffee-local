from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .api import BridgeError
from .const import DOMAIN

class CoffeeEntity(CoordinatorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, key, name):
        super().__init__(coordinator)
        self.key = key
        self._attr_name = name
        self._attr_unique_id = coordinator.device_id + '_' + key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.device_id)}, name='Coffee machine',
            manufacturer="De’Longhi", model=coordinator.data['device']['model'],
        )

    @property
    def available(self):
        return super().available and self.coordinator.data['connection']['ready']

    async def send(self, command):
        try:
            await self.coordinator.client.command(command)
        except BridgeError as exc:
            raise HomeAssistantError(str(exc)) from exc
        finally:
            await self.coordinator.async_request_refresh()
