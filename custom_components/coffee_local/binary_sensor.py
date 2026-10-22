from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.const import EntityCategory
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util
from .entity import CoffeeEntity

FLAG_NAMES = {
    'is_watertank_empty': 'Water tank empty',
    'is_watertank_open': 'Water tank missing',
    'is_waste_container_full': 'Grounds container full',
    'is_waste_container_missing': 'Grounds container missing',
}

async def async_setup_entry(hass, entry, async_add_entities):
    c = entry.runtime_data
    async_add_entities([CoffeeFlag(c, key, FLAG_NAMES[key])
                        for key in c.data['binary_fields'] if key in FLAG_NAMES] + [CoffeeConnection(c, 'connected', 'Connected')])

class CoffeeFlag(CoffeeEntity, RestoreEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator, key, name):
        super().__init__(coordinator, key, name)
        self._last_reported = None
        self._last_reported_at = None
        self._capture_reported_value()

    def _capture_reported_value(self):
        fields = self.coordinator.data['fields']
        # Standby payloads on PrimaDonna Soul can contradict physical conditions.
        # Keep the last awake reading instead of treating standby bits as alarms.
        if fields.get('status_code') in (None, 0):
            return
        value = fields.get(self.key)
        if isinstance(value, bool):
            self._last_reported = value
            self._last_reported_at = dt_util.utcnow().isoformat()

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        previous = await self.async_get_last_state()
        if self._last_reported is None and previous and previous.state in ('on', 'off'):
            self._last_reported = previous.state == 'on'
            self._last_reported_at = previous.attributes.get('last_reported_at')
        self._capture_reported_value()

    def _handle_coordinator_update(self):
        self._capture_reported_value()
        super()._handle_coordinator_update()

    @property
    def available(self):
        return super().available and self._last_reported is not None

    @property
    def is_on(self):
        return self._last_reported

    @property
    def extra_state_attributes(self):
        return {'last_reported_at': self._last_reported_at}

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
