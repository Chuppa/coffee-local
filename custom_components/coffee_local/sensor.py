"""Main machine status only; low-level fields belong in diagnostics."""
from homeassistant.components.sensor import SensorEntity
from .entity import CoffeeEntity

STATUS_NAMES = {
    'in_standby': 'Standby', 'waking_up': 'Heating up',
    'going_to_sleep': 'Shutting down', 'descaling': 'Descaling',
    'preparing_steam': 'Preparing steam', 'ready': 'Ready',
    'rinsing': 'Rinsing', 'preparing_milk': 'Preparing milk',
    'preparing_milk_alt': 'Preparing milk',
    'dispensing_hot_water': 'Dispensing hot water',
    'cleaning_milk': 'Cleaning milk system',
    'preparing_chocolate': 'Preparing chocolate',
}

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([CoffeeSensor(entry.runtime_data, 'status_name', 'Status')])

class CoffeeSensor(CoffeeEntity, SensorEntity):
    @property
    def native_value(self):
        value = self.coordinator.data['fields'].get('status_name')
        return None if value is None else STATUS_NAMES.get(value, 'Unknown')
