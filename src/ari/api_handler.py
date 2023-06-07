import aiohttp
from loguru import logger
import http.client


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
        self.log_api = logger.bind(object_id=f'APIHandler')
        self.count_request = 0

    async def send(self, url: str, method: str, body: dict):
        self.count_request += 1
        number_request = self.count_request

        self.log_api.debug(f'send url={url} meth={method}, number_request={number_request} body={body}')
        response = {'http_code': 503, 'message': '', 'json_response': {}}
        try:
            resp = await self._session.request(method=method, url=url, data=body)
            async with resp:
                if resp.content_type == 'application/json':
                    json_response = await resp.json()
                else:
                    json_response = {}
                if 'error' in json_response:
                    response.update({'message': json_response['error']})
                    self.log_api.warning(f'number_request={number_request} json_response={json_response}')
                else:
                    response.update({'json_response': json_response, 'http_code': resp.status})
                    if 'message' in json_response:
                        response.update({'message': json_response['message']})
        except Exception as e:
            response.update({'message': e})
            self.log_api.error(response)
            self.log_api.exception(e)

        self.log_api.debug(f'number_request={number_request} response={response}')
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

    async def add_channel_to_bridge(self, bridge_id: str, chan_id):
        return await self.send(f'{self._url}/bridges/{bridge_id}/addChannel', 'POST', {'channel': chan_id})

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

    async def destroy_bridge(self, bridge_id: str, include_channels: bool = True, reason_for_channels: str = '21'):
        if include_channels:
            bridge_detail_response = await self.get_bridge_detail(bridge_id)
            if bridge_detail_response.get('http_code') == http.client.NOT_FOUND:
                return bridge_detail_response

            elif bridge_detail_response.get('http_code') == http.client.OK:
                for chan_id in bridge_detail_response.get('json_response').get('channels', []):
                    self.log_api.debug(chan_id)
                    await self.delete_chan(chan_id, reason_for_channels)

        res = await self.send(f'{self._url}/bridges/{bridge_id}', 'DELETE', {})
        return res

    async def create_chan(self, chan_id: str, endpoint: str, callerid: str):
        res = await self.send(f'{self._url}/channels/create',
                              'POST', {
                                  'channelId': chan_id,
                                  'endpoint': endpoint,
                                  'app': self._app,
                                  'variables': {'CALLERID(num)': callerid, 'CALLERID(name)': callerid}
                              })
        return res

    async def dial_chan(self, chan_id: str):
        res = await self.send(f'{self._url}/channels/{chan_id}/dial',
                              'POST', {'timeout': 60})
        return res

    async def start_playback(self, chan_id: str, clip_id: str, name_audio: str, lang: str = 'en', offsetms: int = 0,
                             skipms: int = 3000):
        # media: string - (required) Media URIs to play. Allows comma separated values.
        # lang: string - For sounds, selects language for sound.
        # offsetms: int - Number of milliseconds to skip before playing.
        #                 Only applies to the first URI if multiple media URIs are specified.
        # skipms: int - Number of milliseconds to skip for forward/reverse operations. Default: 3000
        # playbackId: string - Playback ID.

        res = await self.send(f'{self._url}/channels/{chan_id}/play',
                              'POST', {'media': name_audio,
                                       "lang": lang,
                                       "offsetms": offsetms,
                                       "skipms": skipms,
                                       "playbackId": clip_id})
        return res

    async def stop_playback(self, clip_id: str):
        res = await self.send(f'{self._url}/playbacks/{clip_id}', 'DELETE', {})
        return res

    async def create_chan_originate(self, chan_id: str, endpoint: str, callerid: str):
        res = await self.send(f'{self._url}/channels/{chan_id}',
                              'POST', {'channelId': chan_id,
                                       'endpoint': endpoint,
                                       'app': self._app,
                                       "callerId": callerid})
        return res

    async def delete_chan(self, chan_id: str, reason_code: str):
        res = await self.send(f'{self._url}/channels/{chan_id}', 'DELETE', {'reason_code': reason_code})
        return res

    async def create_snoop_chan(self, target_chan_id: str, snoop_id: str, spy: str = 'in', whisper: str = 'none'):
        # spy: string - Direction of audio to spy on
        #   # Default: none
        #   # Allowed values: none, both, out, in
        # whisper: string - Direction of audio to whisper into
        #   # Default: none
        #   # Allowed values: none, both, out, in
        # app: string - (required) Application the snooping channel is placed into
        # appArgs: string - The application arguments to pass to the Stasis application
        # snoopId: string - Unique ID to assign to snooping channel

        res = await self.send(f'{self._url}/channels/{target_chan_id}/snoop',
                              'POST', {
                                  'spy': spy,
                                  'whisper': whisper,
                                  'app': self._app,
                                  'snoopId': snoop_id
                              })
        return res

    async def create_emedia_chan(self, chan_id: str, external_host: str):
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

        res = await self.send(f'{self._url}/channels/externalMedia',
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
        return res

    async def custom_event(self, event_name: str, source: str):
        res = await self.send(f'{self._url}/events/user/{event_name}',
                              'POST', {'application': self._app, 'source': source})
        return res
