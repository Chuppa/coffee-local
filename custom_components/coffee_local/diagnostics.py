async def async_get_config_entry_diagnostics(hass, entry):
    c = entry.runtime_data
    return {
        'bridge_version': c.data.get('bridge_version'),
        'model': c.data['device'].get('model'),
        'connection': c.data['connection'],
        'last_update_success': c.last_update_success,
    }
