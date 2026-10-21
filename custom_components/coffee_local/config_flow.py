import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import selector
from .api import BridgeClient, BridgeAuthError, BridgeError, normalize_url
from .const import DOMAIN, CONF_URL, CONF_TOKEN

class CoffeeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def _validate(self, user_input):
        client = BridgeClient(async_get_clientsession(self.hass), user_input[CONF_URL], user_input[CONF_TOKEN])
        return await client.status()

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input:
            try:
                user_input[CONF_URL] = normalize_url(user_input[CONF_URL])
                data = await self._validate(user_input)
            except BridgeAuthError:
                errors['base'] = 'invalid_auth'
            except (BridgeError, ValueError):
                errors['base'] = 'cannot_connect'
            else:
                await self.async_set_unique_id(data['device']['id'])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title='Coffee ' + data['device']['model'], data=user_input)
        return self.async_show_form(step_id='user', data_schema=vol.Schema({
            vol.Required(CONF_URL, default=(user_input or {}).get(CONF_URL, 'http://homeassistant.local:10281')): str,
            vol.Required(CONF_TOKEN): selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)),
        }), errors=errors)

    async def async_step_reauth(self, entry_data):
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        errors = {}
        entry = self._get_reauth_entry()
        if user_input:
            data = dict(entry.data) | user_input
            try:
                snapshot = await self._validate(data)
                if snapshot['device']['id'] != entry.unique_id:
                    return self.async_abort(reason='wrong_device')
            except BridgeAuthError:
                errors['base'] = 'invalid_auth'
            except (BridgeError, ValueError):
                errors['base'] = 'cannot_connect'
            else:
                return self.async_update_reload_and_abort(entry, data_updates=user_input)
        return self.async_show_form(step_id='reauth_confirm', data_schema=vol.Schema({
            vol.Required(CONF_TOKEN): selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)),
        }), errors=errors)

    async def async_step_reconfigure(self, user_input=None):
        errors = {}
        entry = self._get_reconfigure_entry()
        if user_input:
            try:
                user_input[CONF_URL] = normalize_url(user_input[CONF_URL])
                data = await self._validate(user_input)
                if data['device']['id'] != entry.unique_id:
                    return self.async_abort(reason='wrong_device')
            except BridgeAuthError:
                errors['base'] = 'invalid_auth'
            except (BridgeError, ValueError):
                errors['base'] = 'cannot_connect'
            else:
                return self.async_update_reload_and_abort(entry, data_updates=user_input)
        return self.async_show_form(step_id='reconfigure', data_schema=vol.Schema({
            vol.Required(CONF_URL, default=entry.data[CONF_URL]): str,
            vol.Required(CONF_TOKEN): selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)),
        }), errors=errors)
