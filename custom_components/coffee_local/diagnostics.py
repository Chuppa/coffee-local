"""Non-identifying status bytes help verify model-specific alarm mappings."""
FIELD_KEYS = (
    'status_code', 'status_name', 'action_code', 'action_name', 'accessory_code',
    'accessory_name', 'progress_percent', 'is_busy', 'is_idle',
    'is_watertank_empty', 'is_watertank_open', 'is_waste_container_full',
    'is_waste_container_missing',
)
MONITOR_KEYS = ('direction', 'request_id', 'answer_required', 'accessory',
                'switches', 'alarms', 'status', 'action', 'progress')

async def async_get_config_entry_diagnostics(hass, entry):
    c = entry.runtime_data
    fields = c.data.get('fields', {})
    monitor = c.data.get('monitor', {})
    return {
        'bridge_version': c.data.get('bridge_version'),
        'model': c.data['device'].get('model'),
        'connection': c.data['connection'],
        'last_update_success': c.last_update_success,
        'fields': {key: fields[key] for key in FIELD_KEYS if key in fields},
        'monitor': {key: monitor[key] for key in MONITOR_KEYS if key in monitor},
        'alarm_readings_trusted': fields.get('status_code') not in (None, 0),
    }
