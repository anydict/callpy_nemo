import http.client
from typing import Union

import aiohttp
from loguru import logger

from src.config import Config
from src.custom_dataclasses.api_request import ApiRequest
from src.custom_dataclasses.api_response import ApiResponse
from src.http_clients.base_client import BaseClient


class HttpAsteriskClient(BaseClient):
    def __init__(self, config: Config):
        self._app = config.app
        self._host = config.asterisk_host
        self._port = config.asterisk_port
        auth = aiohttp.BasicAuth(login=str(config.asterisk_login),
                                 password=str(config.asterisk_password),
                                 encoding='utf-8')
        self.log = logger.bind(object_id=self.__class__.__name__)
        super().__init__(auth=auth)
        self.log.info(self.client_session)

    @property
    def url_address(self):
        return f'http://{self._host}:{self._port}'

    async def get_peers(self) -> ApiResponse:
        api_request = ApiRequest(url=f'{self.url_address}/ari/endpoints',
                                 method='GET',
                                 request={})

        return await self.send(api_request)

    async def get_list_by_tech(self, tech: str = 'SIP') -> ApiResponse:
        api_request = ApiRequest(url=f'{self.url_address}/ari/endpoints/{tech}',
                                 method='GET',
                                 request={})

        return await self.send(api_request)

    async def get_detail_endpoint(self, tech: str = 'SIP', resource: str = 'myself') -> ApiResponse:
        api_request = ApiRequest(url=f'{self.url_address}/ari/endpoints/{tech}/{resource}',
                                 method='GET',
                                 request={})

        return await self.send(api_request)

    async def get_chans(self) -> ApiResponse:
        api_request = ApiRequest(url=f'{self.url_address}/ari/channels',
                                 method='GET',
                                 request={})

        return await self.send(api_request)

    async def get_chan_detail(self, chan_id: str) -> ApiResponse:
        api_request = ApiRequest(url=f'{self.url_address}/ari/channels/{chan_id}',
                                 method='GET',
                                 request={})

        return await self.send(api_request)

    async def get_chan_var(self, chan_id: str, variable: str = 'dialplan') -> ApiResponse:
        api_request = ApiRequest(url=f'{self.url_address}/ari/channels/{chan_id}/variable',
                                 method='GET',
                                 request={'variable': variable})

        return await self.send(api_request)

    async def set_chan_var(self, chan_id: str, variable: str, value: Union[str, int]) -> ApiResponse:
        api_request = ApiRequest(url=f'{self.url_address}/ari/channels/{chan_id}/variable',
                                 method='POST',
                                 request={'variable': variable, 'value': str(value)})

        return await self.send(api_request)

    async def get_rtp_stat(self, chan_id: str) -> ApiResponse:
        api_request = ApiRequest(url=f'{self.url_address}/ari/channels/{chan_id}/rtp_statistics',
                                 method='GET',
                                 request={})

        return await self.send(api_request)

    async def get_bridges(self) -> ApiResponse:
        api_request = ApiRequest(url=f'{self.url_address}/ari/bridges',
                                 method='GET',
                                 request={})

        return await self.send(api_request)

    async def get_bridge_detail(self, bridge_id: str) -> ApiResponse:
        api_request = ApiRequest(url=f'{self.url_address}/ari/bridges/{bridge_id}',
                                 method='GET',
                                 request={})

        return await self.send(api_request)

    async def add_channel_to_bridge(self, bridge_id: str, chan_id) -> ApiResponse:
        api_request = ApiRequest(url=f'{self.url_address}/ari/bridges/{bridge_id}/addChannel',
                                 method='POST',
                                 request={'channel': chan_id})

        return await self.send(api_request)

    async def get_asterisk_info(self) -> ApiResponse:
        api_request = ApiRequest(url=f'{self.url_address}/ari/asterisk/info',
                                 method='GET',
                                 request={})

        return await self.send(api_request)

    async def get_asterisk_modules(self) -> ApiResponse:
        api_request = ApiRequest(url=f'{self.url_address}/ari/asterisk/modules',
                                 method='GET',
                                 request={})

        return await self.send(api_request)

    async def get_asterisk_logging(self) -> ApiResponse:
        api_request = ApiRequest(url=f'{self.url_address}/ari/asterisk/logging',
                                 method='GET',
                                 request={})

        return await self.send(api_request)

    async def get_global_var(self, variable: str) -> ApiResponse:
        api_request = ApiRequest(url=f'{self.url_address}/ari/asterisk/variable',
                                 method='GET',
                                 request={'variable': variable})

        return await self.send(api_request)

    async def get_playback_detail(self, playback_id: str) -> ApiResponse:
        api_request = ApiRequest(url=f'{self.url_address}/ari/playbacks/{playback_id}',
                                 method='GET',
                                 request={})

        return await self.send(api_request)

    async def get_sounds(self) -> ApiResponse:
        api_request = ApiRequest(url=f'{self.url_address}/ari/sounds',
                                 method='GET',
                                 request={})

        return await self.send(api_request)

    async def get_sound_detail(self, sound_id) -> ApiResponse:
        api_request = ApiRequest(url=f'{self.url_address}/ari/sounds/{sound_id}',
                                 method='GET',
                                 request={})

        return await self.send(api_request)

    async def subscription(self, event_source: str = 'channel:,bridge:,endpoint:') -> ApiResponse:
        api_request = ApiRequest(url=f'{self.url_address}/ari/applications/{self._app}/subscription',
                                 method='POST',
                                 request={'eventSource': event_source})

        return await self.send(api_request)

    async def create_bridge(self, bridge_id: str, name: str = '') -> ApiResponse:
        api_request = ApiRequest(url=f'{self.url_address}/ari/bridges',
                                 method='POST',
                                 request={'type': 'mixing', 'bridgeId': bridge_id, 'name': name or bridge_id})

        return await self.send(api_request)

    async def destroy_bridge(self,
                             bridge_id: str,
                             include_channels: bool = True,
                             reason_for_channels: int = 21) -> ApiResponse:

        if include_channels:
            bridge_detail_response = await self.get_bridge_detail(bridge_id)
            if bridge_detail_response.http_code == http.client.NOT_FOUND:
                return bridge_detail_response

            elif bridge_detail_response.http_code == http.client.OK:
                for chan_id in bridge_detail_response.result.get('channels', []):
                    self.log.debug(chan_id)
                    await self.delete_chan(chan_id, reason_for_channels)

        api_request = ApiRequest(url=f'{self.url_address}/ari/bridges/{bridge_id}',
                                 method='DELETE',
                                 request={})

        return await self.send(api_request)

    async def create_chan(self, chan_id: str, endpoint: str, callerid: Union[str, int]) -> ApiResponse:
        api_request = ApiRequest(url=f'{self.url_address}/ari/channels/create',
                                 method='POST',
                                 request={
                                     'channelId': chan_id,
                                     'endpoint': endpoint,
                                     'app': self._app,
                                     'variables': {'CALLERID(num)': str(callerid),
                                                   'CALLERID(name)': str(callerid),
                                                   'CONNECTED(num)': str(callerid)}
                                 })

        return await self.send(api_request)

    async def dial_chan(self, chan_id: str, timeout: int = 60) -> ApiResponse:
        api_request = ApiRequest(url=f'{self.url_address}/ari/channels/{chan_id}/dial',
                                 method='POST',
                                 request={'timeout': timeout})

        return await self.send(api_request)

    async def start_chan_playback(self,
                                  chan_id: str,
                                  clip_id: str,
                                  media: str | list[str],
                                  lang: str = 'en',
                                  offsetms: int = 0,
                                  skipms: int = 3000) -> ApiResponse:
        # media: string | list[string] - (required) Media URIs to play
        # lang: string - For sounds, selects language for sound.
        # offsetms: int - Number of milliseconds to skip before playing.
        #                 Only applies to the first URI if multiple media URIs are specified.
        # skipms: int - Number of milliseconds to skip for forward/reverse operations. Default: 3000
        # playbackId: string - Playback ID.
        api_request = ApiRequest(url=f'{self.url_address}/ari/channels/{chan_id}/play',
                                 method='POST',
                                 request={
                                     'media': media,
                                     "lang": lang,
                                     "offsetms": offsetms,
                                     "skipms": skipms,
                                     "playbackId": clip_id
                                 })

        return await self.send(api_request)

    async def start_bridge_playback(self,
                                    bridge_id: str,
                                    clip_id: str,
                                    media: str | list[str],
                                    lang: str = 'en',
                                    offsetms: int = 0,
                                    skipms: int = 3000) -> ApiResponse:
        # media: string | list[string] - (required) Media URIs to play
        # lang: string - For sounds, selects language for sound.
        # offsetms: int - Number of milliseconds to skip before playing.
        #                 Only applies to the first URI if multiple media URIs are specified.
        # skipms: int - Number of milliseconds to skip for forward/reverse operations. Default: 3000
        # playbackId: string - Playback ID.
        api_request = ApiRequest(url=f'{self.url_address}/ari/bridges/{bridge_id}/play',
                                 method='POST',
                                 request={
                                     'media': media,
                                     "lang": lang,
                                     "offsetms": offsetms,
                                     "skipms": skipms,
                                     "playbackId": clip_id
                                 })

        return await self.send(api_request)

    async def stop_playback(self, clip_id: str) -> ApiResponse:
        api_request = ApiRequest(url=f'{self.url_address}/ari/playbacks/{clip_id}',
                                 method='DELETE',
                                 request={})

        return await self.send(api_request)

    async def create_chan_originate(self, chan_id: str, endpoint: str, callerid: str) -> ApiResponse:
        api_request = ApiRequest(url=f'{self.url_address}/ari/channels/{chan_id}',
                                 method='POST',
                                 request={
                                     'channelId': chan_id,
                                     'endpoint': endpoint,
                                     'app': self._app,
                                     "callerId": callerid
                                 })

        return await self.send(api_request)

    async def delete_chan(self,
                          chan_id: str,
                          reason_code: str | int) -> ApiResponse:
        api_request = ApiRequest(url=f'{self.url_address}/ari/channels/{chan_id}',
                                 method='DELETE',
                                 request={"reason_code": str(reason_code)})

        return await self.send(api_request)

    async def create_snoop_chan(self,
                                target_chan_id: str,
                                snoop_id: str,
                                spy: str = 'in',
                                whisper: str = 'none') -> ApiResponse:
        # spy: string - Direction of audio to spy on
        #   # Default: none
        #   # Allowed values: none, both, out, in
        # whisper: string - Direction of audio to whisper into
        #   # Default: none
        #   # Allowed values: none, both, out, in
        # app: string - (required) Application the snooping channel is placed into
        # appArgs: string - The application arguments to pass to the Stasis application
        # snoopId: string - Unique ID to assign to snooping channel

        api_request = ApiRequest(url=f'{self.url_address}/ari/channels/{target_chan_id}/snoop',
                                 method='POST',
                                 request={
                                     'spy': spy,
                                     'whisper': whisper,
                                     'app': self._app,
                                     'snoopId': snoop_id
                                 })

        return await self.send(api_request)

    async def create_emedia_chan(self, chan_id: str, external_host: str) -> ApiResponse:
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
        api_request = ApiRequest(url=f'{self.url_address}/ari/channels/externalMedia',
                                 method='POST',
                                 request={
                                     'channelId': chan_id,
                                     'app': self._app,
                                     'external_host': external_host,
                                     'encapsulation': 'rtp',
                                     'transport': 'udp',
                                     'connection_type': 'client',
                                     'format': 'slin',
                                     'direction': 'both'
                                 })

        return await self.send(api_request)

    async def custom_event(self, event_name: str, source: str) -> ApiResponse:
        api_request = ApiRequest(url=f'{self.url_address}/ari/events/user/{event_name}',
                                 method='POST',
                                 request={'application': self._app, 'source': source})

        return await self.send(api_request)
