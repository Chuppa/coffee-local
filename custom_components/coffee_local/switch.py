from homeassistant.components.switch import SwitchEntity
from .entity import CoffeeEntity

async def async_setup_entry(hass, entry, async_add_entities):
    c = entry.runtime_data
    if {'wakeup', 'standby'} <= c.data['commands'].keys():
        async_add_entities([CoffeePower(c, 'power', 'Power')])

class CoffeePower(CoffeeEntity, SwitchEntity):
    @property
    def is_on(self):
        status = self.coordinator.data['fields'].get('status_code')
        return None if status is None else status != 0

    async def async_turn_on(self, **kwargs):
        await self.send('wakeup')

    async def async_turn_off(self, **kwargs):
        await self.send('standby')
