import asyncio

import aiohttp
from loguru import logger
import http.client

from src.dataclasses.ari_response import AriResponse


class APIHandler(object):
    def __init__(self,
                 host: str = '127.0.0.1',
                 port: int = 8088,
                 login: str = 'asterisk',
                 password: str = 'asterisk',
                 app: str = 'test'):
        self._app = app
        self._host = host
        self._port = port
        self._login = login
        self._password = password
        self._url = f'http://{host}:{port}/ari'
        auth = aiohttp.BasicAuth(login=str(login), password=str(password), encoding='utf-8')
        self._session = aiohttp.ClientSession(auth=auth)
        self.log_api = logger.bind(object_id=f'APIHandler')
        self.count_request = 0

    async def close_session(self):
        if self._session:
            await self._session.close()

    async def send(self,
                   url: str,
                   method: str,
                   body: dict,
                   attempts: int = 3) -> AriResponse:
        self.count_request += 1
        r_id = self.count_request
        response = AriResponse(http_code=0,
                               success=False,
                               message='',
                               json_content=dict())

        self.log_api.debug(f'send url={url} meth={method}, r_id={r_id} body={body}')
        for attempt in range(attempts):
            try:
                result = await self._session.request(method=method, url=url, data=body)
                async with result:
                    response.http_code = result.status
                    response.message = ''
                    if result.content_type == 'application/json':
                        response.json_content = await result.json()
                    else:
                        response.json_content = {}

                    if 'error' in response.json_content:
                        response.message = response.json_content['error']
                        self.log_api.warning(f'[attempt={attempt}] r_id={r_id} json_content={response.json_content}')
                    elif 'message' in response.json_content:
                        response.message = response.json_content['message']
            except Exception as e:
                response.message = str(e)
                if attempt == 0:
                    self.log_api.warning(e)
                else:
                    self.log_api.error(response)
                    self.log_api.exception(e)

            if 200 <= response.http_code <= 299:
                response.success = True

            self.log_api.debug(f'[attempt={attempt}] r_id={r_id} response={response}')

            if response.http_code > 0:
                break
            else:
                # sleep = attempt
                await asyncio.sleep(attempt)

        return response

    async def get_peers(self) -> AriResponse:
        return await self.send(f'{self._url}/endpoints', 'GET', {})

    async def get_list_by_tech(self, tech: str = 'SIP') -> AriResponse:
        return await self.send(f'{self._url}/endpoints/{tech}', 'GET', {})

    async def get_detail_endpoint(self, tech: str = 'SIP', resource: str = 'myself') -> AriResponse:
        return await self.send(f'{self._url}/endpoints/{tech}/{resource}', 'GET', {})

    async def get_chans(self) -> AriResponse:
        return await self.send(f'{self._url}/channels', 'GET', {})

    async def get_chan_detail(self, chan_id: str) -> AriResponse:
        return await self.send(f'{self._url}/channels/{chan_id}', 'GET', {})

    async def get_chan_var(self, chan_id: str, variable: str = 'dialplan') -> AriResponse:
        return await self.send(f'{self._url}/channels/{chan_id}/variable', 'GET', {'variable': variable})

    async def get_rtp_stat(self, chan_id: str) -> AriResponse:
        return await self.send(f'{self._url}/channels/{chan_id}/rtp_statistics', 'GET', {})

    async def get_bridges(self) -> AriResponse:
        return await self.send(f'{self._url}/bridges', 'GET', {})

    async def get_bridge_detail(self, bridge_id: str) -> AriResponse:
        return await self.send(f'{self._url}/bridges/{bridge_id}', 'GET', {})

    async def add_channel_to_bridge(self, bridge_id: str, chan_id) -> AriResponse:
        return await self.send(f'{self._url}/bridges/{bridge_id}/addChannel', 'POST', {'channel': chan_id})

    async def get_asterisk_info(self) -> AriResponse:
        return await self.send(f'{self._url}/asterisk/info', 'GET', {})

    async def get_asterisk_modules(self) -> AriResponse:
        return await self.send(f'{self._url}/asterisk/modules', 'GET', {})

    async def get_asterisk_logging(self) -> AriResponse:
        return await self.send(f'{self._url}/asterisk/logging', 'GET', {})

    async def get_global_var(self, variable: str) -> AriResponse:
        return await self.send(f'{self._url}/asterisk/variable', 'GET', {'variable': variable})

    async def get_playback_detail(self, playback_id: str) -> AriResponse:
        return await self.send(f'{self._url}/playbacks/{playback_id}', 'GET', {})

    async def get_sounds(self) -> AriResponse:
        return await self.send(f'{self._url}/sounds', 'GET', {})

    async def get_sound_detail(self, sound_id) -> AriResponse:
        return await self.send(f'{self._url}/sounds/{sound_id}', 'GET', {})

    async def subscription(self, event_source: str = 'channel:,bridge:,endpoint:') -> AriResponse:
        return await self.send(f'{self._url}/applications/{self._app}/subscription',
                               'POST', {'eventSource': event_source})

    async def create_bridge(self, bridge_id: str, name: str = '') -> AriResponse:
        name = bridge_id if name == '' else name
        return await self.send(f'{self._url}/bridges', 'POST', {'type': 'mixing', 'bridgeId': bridge_id, 'name': name})

    async def destroy_bridge(self,
                             bridge_id: str,
                             include_channels: bool = True,
                             reason_for_channels: str = '21') -> AriResponse:
        if include_channels:
            bridge_detail_response = await self.get_bridge_detail(bridge_id)
            if bridge_detail_response.http_code == http.client.NOT_FOUND:
                return bridge_detail_response

            elif bridge_detail_response.http_code == http.client.OK:
                for chan_id in bridge_detail_response.json_content.get('channels', []):
                    self.log_api.debug(chan_id)
                    await self.delete_chan(chan_id, reason_for_channels)

        return await self.send(f'{self._url}/bridges/{bridge_id}', 'DELETE', {})

    async def create_chan(self, chan_id: str, endpoint: str, callerid: str) -> AriResponse:
        return await self.send(f'{self._url}/channels/create',
                               'POST', {
                                   'channelId': chan_id,
                                   'endpoint': endpoint,
                                   'app': self._app,
                                   'variables': {'CALLERID(num)': callerid, 'CALLERID(name)': callerid}
                               })

    async def dial_chan(self, chan_id: str) -> AriResponse:
        return await self.send(f'{self._url}/channels/{chan_id}/dial',
                               'POST', {'timeout': 60})

    async def start_playback(self,
                             chan_id: str,
                             clip_id: str,
                             name_audio: str,
                             lang: str = 'en',
                             offsetms: int = 0,
                             skipms: int = 3000) -> AriResponse:
        # media: string - (required) Media URIs to play. Allows comma separated values.
        # lang: string - For sounds, selects language for sound.
        # offsetms: int - Number of milliseconds to skip before playing.
        #                 Only applies to the first URI if multiple media URIs are specified.
        # skipms: int - Number of milliseconds to skip for forward/reverse operations. Default: 3000
        # playbackId: string - Playback ID.

        return await self.send(f'{self._url}/channels/{chan_id}/play',
                               'POST', {'media': name_audio,
                                        "lang": lang,
                                        "offsetms": offsetms,
                                        "skipms": skipms,
                                        "playbackId": clip_id})

    async def stop_playback(self, clip_id: str) -> AriResponse:
        return await self.send(f'{self._url}/playbacks/{clip_id}', 'DELETE', {})

    async def create_chan_originate(self, chan_id: str, endpoint: str, callerid: str) -> AriResponse:
        return await self.send(f'{self._url}/channels/{chan_id}',
                               'POST', {'channelId': chan_id,
                                        'endpoint': endpoint,
                                        'app': self._app,
                                        "callerId": callerid})

    async def delete_chan(self,
                          chan_id: str,
                          reason_code: str) -> AriResponse:
        return await self.send(f'{self._url}/channels/{chan_id}', 'DELETE', {'reason_code': reason_code})

    async def create_snoop_chan(self,
                                target_chan_id: str,
                                snoop_id: str,
                                spy: str = 'in',
                                whisper: str = 'none') -> AriResponse:
        # spy: string - Direction of audio to spy on
        #   # Default: none
        #   # Allowed values: none, both, out, in
        # whisper: string - Direction of audio to whisper into
        #   # Default: none
        #   # Allowed values: none, both, out, in
        # app: string - (required) Application the snooping channel is placed into
        # appArgs: string - The application arguments to pass to the Stasis application
        # snoopId: string - Unique ID to assign to snooping channel

        return await self.send(f'{self._url}/channels/{target_chan_id}/snoop',
                               'POST', {
                                   'spy': spy,
                                   'whisper': whisper,
                                   'app': self._app,
                                   'snoopId': snoop_id
                               })

    async def create_emedia_chan(self, chan_id: str, external_host: str) -> AriResponse:
        # channelId: string - The unique id to assign the channel on creation.
        # app: string - (required) Stasis Application to place channel into
        # external_host: string - (required) Hostname/ip:port of external host
        # encapsulation: string - Payload encapsulation protocol
        #   # Default: rtp
        #   # Allowed values: rtp, audiosocket
        # transport: string - Transport protocol
        #   # Default: udp
        #   # Allowed values: udp, tcp
        # connection_type: string - Connection type (client/server)
        #   # Default: client
        #   # Allowed values: client
        # format: string - (required) Format to encode audio in
        # direction: string - External media direction
        #   # Default: both
        #   # Allowed values: both
        # data: string - An arbitrary data field

        return await self.send(f'{self._url}/channels/externalMedia',
                               'POST', {
                                   'channelId': chan_id,
                                   'app': self._app,
                                   'external_host': external_host,
                                   'encapsulation': 'rtp',
                                   'transport': 'udp',
                                   'connection_type': 'client',
                                   'format': 'slin16',
                                   'direction': 'both'
                               })

    async def custom_event(self, event_name: str, source: str) -> AriResponse:
        return await self.send(f'{self._url}/events/user/{event_name}',
                               'POST', {'application': self._app, 'source': source})
