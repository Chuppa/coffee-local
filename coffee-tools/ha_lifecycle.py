"""Run inside the official HA image; exercise real config flow and entity lifecycle."""
import asyncio
import copy
import importlib
import json
from pathlib import Path
import shutil
import tempfile

from aiohttp import web
from homeassistant import bootstrap, loader
from homeassistant.core import HomeAssistant
from homeassistant.const import __version__

ROOT = Path('/repo')

async def main():
    payload = {
        'api_version': 1, 'bridge_version': '0.1.0',
        'device': {'id': 'SIMULATOR', 'model': 'ECAM612'},
        'connection': {'ready': False, 'registered': False, 'keys_ready': False, 'monitor_age_seconds': None, 'last_error': None},
        'fields': {}, 'commands': {'wakeup': 'Turn On', 'standby': 'Turn Off', 'espresso': 'Espresso', 'stop': 'Stop'},
        'binary_fields': ['is_busy', 'is_watertank_empty'], 'last_command': None,
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
    with tempfile.TemporaryDirectory() as directory:
        shutil.copytree(ROOT / 'custom_components', Path(directory) / 'custom_components', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        hass = HomeAssistant(directory)
        loader.async_setup(hass)
        try:
            result = await bootstrap.async_from_config_dict({'homeassistant': {
                'name': 'Coffee test', 'latitude': 0, 'longitude': 0, 'elevation': 0,
                'unit_system': 'metric', 'time_zone': 'UTC',
            }}, hass)
            assert result is not None
            await hass.async_start()
            first = await hass.config_entries.flow.async_init('coffee_local', context={'source': 'user'})
            assert first['type'] == 'form', first
            result = await hass.config_entries.flow.async_configure(first['flow_id'], {
                'url': f'http://127.0.0.1:{port}', 'api_token': 'x' * 32,
            })
            assert result['type'] == 'create_entry', result
            await hass.async_block_till_done()
            entry = result['result']
            assert entry.runtime_data.data['connection']['ready'] is False
            states = hass.states.async_all()
            coffee_states = [state for state in states if 'coffee_machine' in state.entity_id]
            assert len(coffee_states) == 10, [(s.entity_id,s.state) for s in states]
            assert hass.states.get('binary_sensor.coffee_machine_connected').state == 'off'
            assert hass.states.get('switch.coffee_machine_power').state == 'unavailable'
            payload['connection']['ready'] = True
            payload['fields'] = {'status_code': 7, 'status_name': 'ready', 'is_busy': False, 'is_watertank_empty': False, 'progress_percent': 0}
            await entry.runtime_data.async_refresh()
            await hass.async_block_till_done()
            assert hass.states.get('switch.coffee_machine_power').state == 'on'
            assert hass.states.get('sensor.coffee_machine_status').state == 'ready'
            # Reload HA entry against an existing bridge; it issues no configure request.
            assert await hass.config_entries.async_reload(entry.entry_id)
            await hass.async_block_till_done()
            assert hass.states.get('switch.coffee_machine_power').state == 'on'
            # A bridge outage must mark entities unavailable and recover on refresh.
            bridge_url = entry.runtime_data.client.url
            entry.runtime_data.client.url = "http://127.0.0.1:1"
            await entry.runtime_data.async_refresh()
            await hass.async_block_till_done()
            assert hass.states.get('switch.coffee_machine_power').state == 'unavailable'
            entry.runtime_data.client.url = bridge_url
            await entry.runtime_data.async_refresh()
            await hass.async_block_till_done()
            assert hass.states.get('switch.coffee_machine_power').state == 'on'
            # A new bridge identity must never silently control a different machine.
            payload['device']['id'] = 'DIFFERENT-MACHINE'
            await entry.runtime_data.async_refresh()
            await hass.async_block_till_done()
            assert hass.states.get('switch.coffee_machine_power').state == 'unavailable'
            payload['device']['id'] = 'SIMULATOR'
            await entry.runtime_data.async_refresh()
            await hass.async_block_till_done()
            assert hass.states.get('switch.coffee_machine_power').state == 'on'
            # Tokens and LAN details must not appear in downloadable diagnostics.
            from custom_components.coffee_local.diagnostics import async_get_config_entry_diagnostics
            diagnostics = await async_get_config_entry_diagnostics(hass, entry)
            assert 'x' * 32 not in json.dumps(diagnostics)
            # Missing server package is irrelevant: requirements are empty and modules
            # import successfully in the official HA runtime.
            assert json.loads((Path(directory) / 'custom_components/coffee_local/manifest.json').read_text())['requirements'] == []
            assert await hass.config_entries.async_unload(entry.entry_id)
            await hass.async_block_till_done()
            print(f'HA {__version__}: real config flow, 10 entities, offline→online, reload, identity guard, recovery, diagnostics and unload passed')
        finally:
            await hass.async_stop(force=True)
            await runner.cleanup()

asyncio.run(main())
