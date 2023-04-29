import aiohttp
from loguru import logger


class APIHandler(object):
    def __init__(self, host: str = '127.0.0.1', port: int = 8088,
                 login: str = 'asterisk', password: str = 'asterisk', app: str = 'test'):
        self._app = app
        self._host = host
        self._port = port
        self._login = login
        self._password = password
        self._url = f'http://{host}:{port}/ari'
        auth = aiohttp.BasicAuth(login=str(login), password=str(password), encoding='utf-8')
        self._session = aiohttp.ClientSession(auth=auth)
        self.logapi = logger.bind(object_id=f'APIHandler')

    async def send(self, url: str, method: str, body: dict):
        self.logapi.debug(f'send url={url} meth={method}, body={body}')
        response = {'http_code': 503}
        try:
            resp = await self._session.request(method=method, url=url, data=body)
            async with resp:
                if resp.content_type == 'application/json':
                    json_response = await resp.json()
                else:
                    json_response = {}
                if 'error' in json_response:
                    response.update({'error': json_response['error']})
                    self.logapi.warning(f'json_response={json_response}')
                else:
                    response.update({'json_response': json_response, 'http_code': resp.status})
        except Exception as e:
            response.update({'error': e})
            self.logapi.error(response)
            self.logapi.exception(e)

        self.logapi.debug(f'response={response}')
        return response

    async def get_peers(self):
        return await self.send(f'{self._url}/endpoints', 'GET', {})

    async def get_list_by_tech(self, tech: str = 'SIP'):
        return await self.send(f'{self._url}/endpoints/{tech}', 'GET', {})

    async def get_detail_endpoint(self, tech: str = 'SIP', resource: str = 'myself'):
        return await self.send(f'{self._url}/endpoints/{tech}/{resource}', 'GET', {})

    async def get_chans(self):
        return await self.send(f'{self._url}/channels', 'GET', {})

    async def get_chan_detail(self, chan_id: str):
        return await self.send(f'{self._url}/channels/{chan_id}', 'GET', {})

    async def get_chan_var(self, chan_id: str, variable: str = 'dialplan'):
        return await self.send(f'{self._url}/channels/{chan_id}/variable', 'GET', {'variable': variable})

    async def get_rtp_stat(self, chan_id: str):
        return await self.send(f'{self._url}/channels/{chan_id}/rtp_statistics', 'GET', {})

    async def get_bridges(self):
        return await self.send(f'{self._url}/bridges', 'GET', {})

    async def get_bridge_detail(self, bridge_id: str):
        return await self.send(f'{self._url}/bridges/{bridge_id}', 'GET', {})

    async def get_asterisk_info(self):
        return await self.send(f'{self._url}/asterisk/info', 'GET', {})

    async def get_asterisk_modules(self):
        return await self.send(f'{self._url}/asterisk/modules', 'GET', {})

    async def get_asterisk_logging(self):
        return await self.send(f'{self._url}/asterisk/logging', 'GET', {})

    async def get_global_var(self, variable: str):
        return await self.send(f'{self._url}/asterisk/variable', 'GET', {'variable': variable})

    async def get_playback_detail(self, playback_id: str):
        return await self.send(f'{self._url}/playbacks/{playback_id}', 'GET', {})

    async def get_sounds(self):
        return await self.send(f'{self._url}/sounds', 'GET', {})

    async def get_sound_detail(self, sound_id):
        return await self.send(f'{self._url}/sounds/{sound_id}', 'GET', {})

    async def subscription(self, event_source: str = 'channel:,bridge:,endpoint:'):
        res = await self.send(f'{self._url}/applications/{self._app}/subscription',
                              'POST', {'eventSource': event_source})
        return res

    async def create_bridge(self, bridge_id: str, name: str = ''):
        name = bridge_id if name == '' else name
        res = await self.send(f'{self._url}/bridges', 'POST', {'type': 'mixing', 'bridgeId': bridge_id, 'name': name})
        return res

    async def create_chan(self, chan_id: str, endpoint: str, callerid: str):
        res = await self.send(f'{self._url}/channels/{chan_id}',
                              'POST', {'channelId': chan_id,
                                       'endpoint': endpoint,
                                       'app': self._app,
                                       "callerId": callerid})
        return res

    async def custom_event(self, event_name: str, source: str):
        res = await self.send(f'{self._url}/events/user/{event_name}',
                              'POST', {'application': self._app, 'source': source})
        return res
