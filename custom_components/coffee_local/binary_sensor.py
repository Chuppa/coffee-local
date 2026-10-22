from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.const import EntityCategory
from .entity import CoffeeEntity

FLAG_NAMES = {
    'is_busy': 'Busy',
    'is_watertank_empty': 'Water tank empty',
    'is_watertank_open': 'Water tank open',
    'is_waste_container_full': 'Grounds container full',
    'is_waste_container_missing': 'Grounds container missing',
    'is_milk_fridge_warning': 'Milk refrigeration warning',
}

async def async_setup_entry(hass, entry, async_add_entities):
    c = entry.runtime_data
    async_add_entities([CoffeeFlag(c, key, FLAG_NAMES[key])
                        for key in c.data['binary_fields'] if key in FLAG_NAMES] + [CoffeeConnection(c, 'connected', 'Connected')])

class CoffeeFlag(CoffeeEntity, BinarySensorEntity):
    @property
    def device_class(self):
        return BinarySensorDeviceClass.RUNNING if self.key == 'is_busy' else BinarySensorDeviceClass.PROBLEM

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
