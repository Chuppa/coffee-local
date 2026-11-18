from homeassistant.components.switch import SwitchEntity
from .entity import CoffeeEntity
from .api import BridgeError
from homeassistant.exceptions import HomeAssistantError

async def async_setup_entry(hass, entry, async_add_entities):
    c = entry.runtime_data
    if {'wakeup', 'standby'} <= c.data['commands'].keys():
        async_add_entities([CoffeePower(c, 'power', 'Power')])

class CoffeePower(CoffeeEntity, SwitchEntity):
    @property
    def available(self):
        # The bridge can accept a target while the machine is reconnecting.
        return self.coordinator.last_update_success

    @property
    def extra_state_attributes(self):
        request = self.coordinator.data.get('power_control', {}).get('request') or {}
        return {'requested_power': request.get('on'), 'retrying': request.get('state') == 'pending',
                'attempts': request.get('attempts', 0)}

    @property
    def is_on(self):
        status = self.coordinator.data['fields'].get('status_code')
        return None if status is None else status != 0

    async def async_turn_on(self, **kwargs):
        await self.set_power(True)

    async def async_turn_off(self, **kwargs):
        await self.set_power(False)

    async def set_power(self, on):
        if self.coordinator.data.get('power_control', {}).get('supported') is not True:
            raise HomeAssistantError('Update Coffee Local Bridge to 2026.11.10 or later for reliable power control')
        try:
            await self.coordinator.client.power(on, self.coordinator.device_id)
        except BridgeError as exc:
            raise HomeAssistantError(str(exc)) from exc
        finally:
            await self.coordinator.async_request_refresh()
