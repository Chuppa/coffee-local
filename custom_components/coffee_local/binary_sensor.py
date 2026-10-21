from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.const import EntityCategory
from .entity import CoffeeEntity

async def async_setup_entry(hass, entry, async_add_entities):
    c = entry.runtime_data
    async_add_entities([CoffeeFlag(c, key, key.removeprefix('is_').replace('_', ' ').capitalize())
                        for key in c.data['binary_fields']] + [CoffeeConnection(c, 'connected', 'Connected')])

class CoffeeFlag(CoffeeEntity, BinarySensorEntity):
    @property
    def is_on(self):
        return self.coordinator.data['fields'].get(self.key)

class CoffeeConnection(CoffeeEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def available(self):
        return self.coordinator.last_update_success

    @property
    def is_on(self):
        return self.coordinator.data['connection']['ready']

    @property
    def extra_state_attributes(self):
        return self.coordinator.data['connection'] | {'last_command': self.coordinator.data.get('last_command')}
