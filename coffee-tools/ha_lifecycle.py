"""Exercise basic entities, standby caching and restoration in real Home Assistant."""
import asyncio
import json
from pathlib import Path
import shutil
import sys
import tempfile

from aiohttp import web
from homeassistant import bootstrap, loader
from homeassistant.core import HomeAssistant
from homeassistant.const import __version__
from homeassistant.helpers import entity_registry as er

ROOT = Path('/repo')

async def start_hass(directory):
    hass = HomeAssistant(directory)
    loader.async_setup(hass)
    result = await bootstrap.async_from_config_dict({'homeassistant': {
        'name': 'Coffee test', 'latitude': 0, 'longitude': 0, 'elevation': 0,
        'unit_system': 'metric', 'time_zone': 'UTC',
    }}, hass)
    assert result is not None
    await hass.async_start()
    await hass.async_block_till_done()
    return hass

async def main():
    # Use Marketplace's actual post-install validator when present in core.
    # Stable HA before 2026.11 continues to be tested through the loader below.
    from importlib.util import find_spec
    if find_spec('homeassistant.components.marketplace') is not None:
        from homeassistant.components.marketplace.repositories.integration import (
            _check_loadable_manifest, _validated_domain,
        )
        manifest = json.loads((ROOT / 'custom_components/coffee_local/manifest.json').read_text())
        assert _validated_domain(manifest['domain']) == 'coffee_local'
        assert not (Path(loader.__file__).parent / 'components/coffee_local').exists()
        _check_loadable_manifest(ROOT / 'custom_components/coffee_local', 'coffee_local')
        print(f'HA {__version__}: built-in Marketplace manifest/domain checks passed', flush=True)
    payload = {
        'api_version': 1, 'bridge_version': '2026.10.1',
        'device': {'id': 'SIMULATOR', 'model': 'ECAM612'},
        'connection': {'ready': False, 'registered': False, 'keys_ready': False,
                       'monitor_age_seconds': None, 'last_error': None},
        'fields': {},
        'monitor': {'status': 7, 'alarms': [0, 0, 0, 0], 'secret_extra': 'DO-NOT-EXPORT'},
        'commands': {'wakeup': 'Turn On', 'standby': 'Turn Off', 'espresso': 'Espresso', 'stop': 'Stop'},
        'binary_fields': ['is_busy', 'is_idle', 'is_watertank_empty', 'is_watertank_open',
                          'is_waste_container_full', 'is_waste_container_missing', 'is_milk_fridge_warning'],
        'last_command': None,
    }
    async def status(request):
        if request.headers.get('Authorization') != 'Bearer ' + 'x' * 32:
            raise web.HTTPUnauthorized()
        return web.json_response(payload)
    bridge = web.Application()
    bridge.router.add_get('/api/v1/status', status)
    runner = web.AppRunner(bridge)
    await runner.setup()
    site = web.TCPSite(runner, '127.0.0.1', 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    try:
        with tempfile.TemporaryDirectory() as directory:
            shutil.copytree(ROOT / 'custom_components', Path(directory) / 'custom_components',
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            hass = await start_hass(directory)
            try:
                first = await hass.config_entries.flow.async_init('coffee_local', context={'source': 'user'})
                result = await hass.config_entries.flow.async_configure(first['flow_id'], {
                    'url': f'http://127.0.0.1:{port}', 'api_token': 'x' * 32,
                })
                assert result['type'] == 'create_entry', result
                await hass.async_block_till_done()
                entry = result['result']
                registry = er.async_get(hass)
                def entity_id(domain, key):
                    return registry.async_get_entity_id(domain, 'coffee_local', 'SIMULATOR_' + key)
                ids = {key: entity_id('binary_sensor', key) for key in payload['binary_fields']}
                assert len(er.async_entries_for_config_entry(registry, entry.entry_id)) == 7
                assert hass.states.get('switch.coffee_machine_power').state == 'unavailable'
                assert hass.states.get('binary_sensor.coffee_machine_connected').state == 'off'
                for removed in ('is_busy', 'is_idle', 'is_milk_fridge_warning'):
                    assert ids[removed] is None
                assert entity_id('sensor', 'accessory_name') is None
                assert entity_id('sensor', 'progress_percent') is None
                assert registry.async_get(ids['is_watertank_open']).original_name == 'Water tank missing'
                payload['connection']['ready'] = True
                payload['fields'] = {'status_code': 7, 'status_name': 'ready', 'is_busy': False,
                                     'is_watertank_empty': False, 'is_watertank_open': False,
                                     'is_waste_container_full': True, 'is_waste_container_missing': False,
                                     'secret_extra': 'DO-NOT-EXPORT'}
                await entry.runtime_data.async_refresh()
                assert hass.states.get('switch.coffee_machine_power').state == 'on'
                assert hass.states.get('sensor.coffee_machine_status').state == 'Ready'
                assert hass.states.get(ids['is_watertank_empty']).state == 'off'
                assert hass.states.get(ids['is_waste_container_full']).state == 'on'
                # Contradictory standby payload must not overwrite the last report.
                payload['fields'].update(status_code=0, status_name='in_standby', is_busy=True,
                                         is_watertank_empty=True, is_waste_container_full=False)
                await entry.runtime_data.async_refresh()
                assert hass.states.get('switch.coffee_machine_power').state == 'off'
                assert hass.states.get('sensor.coffee_machine_status').state == 'Standby'
                assert hass.states.get(ids['is_watertank_empty']).state == 'off'
                assert hass.states.get(ids['is_waste_container_full']).state == 'on'
                assert hass.states.get(ids['is_watertank_empty']).attributes['last_reported_at']
                # Seed old entities to verify upgrade cleanup; preserve kept IDs/names.
                retired = []
                for domain, key in [('button', 'espresso'), ('sensor', 'action_name'),
                                    ('sensor', 'accessory_name'), ('sensor', 'progress_percent'),
                                    ('binary_sensor', 'is_busy'), ('binary_sensor', 'is_idle'),
                                    ('binary_sensor', 'is_milk_fridge_warning')]:
                    old = registry.async_get_or_create(domain, 'coffee_local', 'SIMULATOR_' + key,
                                                       config_entry=entry, suggested_object_id='legacy_' + key)
                    retired.append(old.entity_id)
                registry.async_update_entity('switch.coffee_machine_power', name='Kitchen coffee power')
                assert await hass.config_entries.async_reload(entry.entry_id)
                await hass.async_block_till_done()
                assert all(registry.async_get(eid) is None for eid in retired)
                assert registry.async_get('switch.coffee_machine_power').name == 'Kitchen coffee power'
                assert hass.states.get(ids['is_watertank_empty']).state == 'off'
                assert hass.states.get(ids['is_waste_container_full']).state == 'on'
                # Bridge outage/recovery and identity guard remain intact.
                url = entry.runtime_data.client.url
                entry.runtime_data.client.url = 'http://127.0.0.1:1'
                await entry.runtime_data.async_refresh()
                assert hass.states.get('switch.coffee_machine_power').state == 'unavailable'
                entry.runtime_data.client.url = url
                await entry.runtime_data.async_refresh()
                payload['device']['id'] = 'DIFFERENT'
                await entry.runtime_data.async_refresh()
                assert hass.states.get('switch.coffee_machine_power').state == 'unavailable'
                payload['device']['id'] = 'SIMULATOR'
                await entry.runtime_data.async_refresh()
                from custom_components.coffee_local.diagnostics import async_get_config_entry_diagnostics
                diagnostics = await async_get_config_entry_diagnostics(hass, entry)
                assert diagnostics['fields']['status_code'] == 0
                assert diagnostics['monitor']['alarms'] == [0, 0, 0, 0]
                assert diagnostics['alarm_readings_trusted'] is False
                for secret in ('x' * 32, 'DO-NOT-EXPORT', 'SIMULATOR'):
                    assert secret not in json.dumps(diagnostics)
                # A fresh awake report replaces cached values.
                payload['fields'].update(status_code=7, status_name='ready')
                await entry.runtime_data.async_refresh()
                assert hass.states.get(ids['is_watertank_empty']).state == 'on'
                assert hass.states.get(ids['is_waste_container_full']).state == 'off'
                payload['fields'].update(is_watertank_empty=False, is_waste_container_full=True)
                await entry.runtime_data.async_refresh()
                payload['fields'].update(status_code=0, status_name='in_standby',
                                         is_watertank_empty=True, is_waste_container_full=False)
                await entry.runtime_data.async_refresh()
            finally:
                await hass.async_stop(force=True)
            # A restart is a fresh OS process, not a second HA instance sharing
            # native libraries and process-global resources in one interpreter.
            child = await asyncio.create_subprocess_exec(
                sys.executable, __file__, '--restore', directory,
                ids['is_watertank_empty'], ids['is_waste_container_full'])
            assert await child.wait() == 0, 'Fresh-process restore check failed'
            print(f'HA {__version__}: 7 basic entities, migration, standby cache, full restart, '
                  'fresh reports, identity guard, outage/recovery and redacted diagnostics passed')
    finally:
        await runner.cleanup()

async def check_restored(directory, water_id, grounds_id):
    hass = await start_hass(directory)
    try:
        assert hass.states.get('switch.coffee_machine_power').state == 'off'
        assert hass.states.get(water_id).state == 'off'
        assert hass.states.get(grounds_id).state == 'on'
        entry = hass.config_entries.async_entries('coffee_local')[0]
        assert await hass.config_entries.async_unload(entry.entry_id)
    finally:
        await hass.async_stop(force=True)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--restore':
        asyncio.run(check_restored(*sys.argv[2:]))
    else:
        asyncio.run(main())
