from homeassistant.components.button import ButtonEntity
from .entity import CoffeeEntity

async def async_setup_entry(hass, entry, async_add_entities):
    c = entry.runtime_data
    async_add_entities([CoffeeButton(c, key, name) for key, name in c.data['commands'].items()
                        if key not in ('wakeup', 'standby')])

class CoffeeButton(CoffeeEntity, ButtonEntity):
    async def async_press(self):
        await self.send(self.key)
