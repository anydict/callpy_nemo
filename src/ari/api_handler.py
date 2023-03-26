import aiohttp
from aiohttp import ClientSession
from loguru import logger


class APIHandler(object):
    _host = '127.0.0.1'
    _port = 8088
    _url = f'http://{_host}:{_port}/ari'
    _login = 'asterisk'
    _password = 'asterisk'
    _session: ClientSession

    def __init__(self):
        auth = aiohttp.BasicAuth(login=str(self._login), password=str(self._password), encoding='utf-8')
        self._session = aiohttp.ClientSession(auth=auth)

    async def send(self, url: str, method: str, body: dict):
        response = {'http_code': 503}
        try:
            resp = await self._session.request(method=method, url=url, data=body)
            async with resp:
                json_res = await resp.json()
                response.update({'data': json_res, 'http_code': resp.status})
        except Exception as e:
            response.update({'msg': e})
            logger.error(response)

        logger.debug(response)
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

    async def create_bridge(self, bridge_id: str, name: str = ''):
        name = bridge_id if name == '' else name
        return await self.send(f'{self._url}/bridges', 'POST', {'type': 'mixing', 'bridgeId': bridge_id, 'name': name})
