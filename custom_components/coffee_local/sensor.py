from homeassistant.components.sensor import SensorEntity
from .entity import CoffeeEntity

async def async_setup_entry(hass, entry, async_add_entities):
    c = entry.runtime_data
    async_add_entities([CoffeeSensor(c, key, name) for key, name in (
        ('status_name', 'Status'), ('action_name', 'Action'),
        ('accessory_name', 'Accessory'), ('progress_percent', 'Progress'),
    )])

class CoffeeSensor(CoffeeEntity, SensorEntity):
    @property
    def native_value(self):
        return self.coordinator.data['fields'].get(self.key)

    @property
    def native_unit_of_measurement(self):
        return '%' if self.key == 'progress_percent' else None
