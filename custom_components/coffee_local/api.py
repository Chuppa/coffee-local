"""Small HTTP client; no protocol/server package is imported into HA."""
import asyncio
from urllib.parse import urlsplit
import uuid
from aiohttp import ClientError, ClientTimeout

class BridgeError(Exception):
    pass

class BridgeAuthError(BridgeError):
    pass


def normalize_url(value):
    parsed = urlsplit(value.rstrip('/'))
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment:
        raise ValueError('Use a bridge origin URL such as http://192.168.1.10:10281')
    parsed.port  # validate port
    return value.rstrip('/')


def validate_snapshot(data):
    if not isinstance(data, dict) or data.get('api_version') != 1:
        raise BridgeError('Unsupported bridge API version')
    if not isinstance(data.get('device'), dict) or not isinstance(data['device'].get('id'), str) or not data['device']['id'] or not isinstance(data['device'].get('model'), str):
        raise BridgeError('Bridge device identity missing')
    if not isinstance(data.get('connection'), dict) or type(data['connection'].get('ready')) is not bool:
        raise BridgeError('Bridge readiness missing')
    if not isinstance(data.get('fields'), dict) or not isinstance(data.get('commands'), dict) or not isinstance(data.get('binary_fields'), list):
        raise BridgeError('Invalid bridge capabilities')
    if any(not isinstance(key, str) for key in data['binary_fields']) or any(not isinstance(v, str) for v in data['commands'].values()):
        raise BridgeError('Invalid bridge capability types')
    return data

class BridgeClient:
    def __init__(self, session, url, token):
        self.session = session
        self.url = normalize_url(url)
        self.token = token

    async def request(self, method, path, body=None):
        try:
            async with self.session.request(method, self.url + path, json=body,
                headers={'Authorization': 'Bearer ' + self.token},
                timeout=ClientTimeout(total=8), allow_redirects=False) as response:
                if response.status in (401, 403):
                    raise BridgeAuthError('Bridge API token was rejected')
                if response.status >= 300:
                    raise BridgeError(f'Bridge returned HTTP {response.status}; command not confirmed')
                return await response.json()
        except (ClientError, asyncio.TimeoutError, ValueError) as exc:
            raise BridgeError('Cannot communicate with coffee bridge') from exc

    async def status(self):
        return validate_snapshot(await self.request('GET', '/api/v1/status'))

    async def command(self, alias):
        request_id = str(uuid.uuid4())
        receipt = await self.request('POST', '/api/v1/commands', {'command': alias, 'request_id': request_id})
        if receipt.get('id') != request_id or receipt.get('state') not in ('queued', 'delivered'):
            raise BridgeError('Bridge returned an invalid command receipt')
        # Do not retry the POST: a timeout may mean the machine already received it.
        for _ in range(8):
            if receipt['state'] == 'delivered':
                return receipt
            await asyncio.sleep(2)
            receipt = await self.request('GET', '/api/v1/commands/' + request_id)
            if receipt.get('state') in ('expired', 'session_changed'):
                raise BridgeError('Command expired before delivery; it will not be replayed')
        raise BridgeError('Command delivery not confirmed; check machine before trying again')
