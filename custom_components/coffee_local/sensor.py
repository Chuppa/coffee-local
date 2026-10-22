"""Useful machine status with readable labels instead of protocol tokens."""
from homeassistant.components.sensor import SensorEntity
from .entity import CoffeeEntity

STATUS_NAMES = {
    'in_standby': 'Standby',
    'waking_up': 'Heating up',
    'going_to_sleep': 'Shutting down',
    'descaling': 'Descaling',
    'preparing_steam': 'Preparing steam',
    'ready': 'Ready',
    'rinsing': 'Rinsing',
    'preparing_milk': 'Preparing milk',
    'preparing_milk_alt': 'Preparing milk',
    'dispensing_hot_water': 'Dispensing hot water',
    'cleaning_milk': 'Cleaning milk system',
    'preparing_chocolate': 'Preparing chocolate',
}
ATTACHMENT_NAMES = {
    'none': 'No attachment',
    'hot_water_spout': 'Hot water spout',
    'latte_crema_hot': 'Milk jug (hot)',
    'latte_crema_hot_clean': 'Milk jug (hot, cleaning mode)',
    'latte_crema_cool': 'Milk jug (cold)',
    'latte_crema_cool_clean': 'Milk jug (cold, cleaning mode)',
    'chocolate': 'Chocolate attachment',
}

async def async_setup_entry(hass, entry, async_add_entities):
    c = entry.runtime_data
    async_add_entities([CoffeeSensor(c, key, name) for key, name in (
        ('status_name', 'Status'), ('accessory_name', 'Attachment'),
        ('progress_percent', 'Progress'),
    )])

class CoffeeSensor(CoffeeEntity, SensorEntity):
    @property
    def native_value(self):
        value = self.coordinator.data['fields'].get(self.key)
        if value is None:
            return None
        if self.key == 'status_name':
            return STATUS_NAMES.get(value, 'Unknown')
        if self.key == 'accessory_name':
            return ATTACHMENT_NAMES.get(value, 'Unknown')
        return value

    @property
    def native_unit_of_measurement(self):
        return '%' if self.key == 'progress_percent' else None
