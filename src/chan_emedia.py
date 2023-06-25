import asyncio
import json
from datetime import datetime

from aiohttp import ClientConnectorError

from src.chan import Chan
import http.client
import aiohttp


class ChanEmedia(Chan):
    """For work with ExternalMedia channel"""

    external_host: str = ''
    em_host: str = ''
    em_port: int = 0
    _em_ssrc: int = 0

    @property
    async def em_ssrc(self):
        for i in range(4):
            if self._em_ssrc > 0:
                return self._em_ssrc
            await asyncio.sleep(0.5)
        self.log.error('no found em_ssrc!')
        return self._em_ssrc

    @em_ssrc.setter
    def em_ssrc(self, ssrc: int):
        self._em_ssrc = ssrc

    async def make_get_request(self, url, params=None, description=''):
        """
        This is an asynchronous function that makes a GET request to a specified URL with optional parameters.

        @param self - the instance of the class
        @param url - the URL to make the GET request to
        @param params - optional parameters to include in the GET request
        @return a tuple containing the status code and data from the response
        """
        try:
            async with aiohttp.ClientSession() as session:
                headers = {'druid': self.room.druid, 'description': description}
                async with session.get(url, params=params, headers=headers) as response:
                    self.log.info(f'fetch_json url={url} params={params}')
                    status = response.status
                    body = await response.text()
                    try:
                        data = json.loads(body)
                    except json.JSONDecodeError:
                        self.log.error(f'JSONDecodeError with body={body}')
                        data = None
                    return status, data
        except ClientConnectorError:
            return 503, {"msg": "ClientConnectorError"}

    async def make_post_request(self, url, data=None, description=''):
        try:
            async with aiohttp.ClientSession() as session:
                headers = {'Content-type': 'application/json',
                           'Accept': 'text/plain',
                           'druid': self.room.druid,
                           'description': description}
                async with session.post(url, data=json.dumps(data), headers=headers) as response:
                    self.log.info(f'fetch_json url={url} params={data}')
                    status = response.status
                    body = await response.text()
                    try:
                        data_response = json.loads(body)
                    except json.JSONDecodeError:
                        self.log.error(f'JSONDecodeError with body={body}')
                        data_response = None
                    return status, data_response
        except ClientConnectorError:
            return 503, {"msg": "ClientConnectorError"}

    async def send_event_create(self, trigger_tag: str):
        """
        This is an asynchronous function that reports the start of an event manager.

        @return None
        """
        self.log.info('send_event_create')
        statuses = self.room.tags_statuses.get(trigger_tag)
        if statuses is None \
                or statuses.get('ChannelVarset#UNICASTRTP_LOCAL_ADDRESS') is None \
                or statuses.get('ChannelVarset#UNICASTRTP_LOCAL_PORT') is None:
            self.log.error(f'invalid statuses')
            self.log.error(statuses)
            return

        try:
            self.em_host = statuses.get('ChannelVarset#UNICASTRTP_LOCAL_ADDRESS').get('value')
            self.em_port = statuses.get('ChannelVarset#UNICASTRTP_LOCAL_PORT').get('value')
            event_time = statuses.get('ChannelVarset#BRIDGEPEER').get('external_time')

            url = 'http://127.0.0.1:7005/events'
            data = {
                "event_name": "CREATE",
                "event_time": event_time,
                "druid": self.room.druid,
                "chan_id": self.chan_id,
                "send_time": datetime.now().isoformat(),
                "token": "NE1K0Vz4pPa9PRJ+JtAibBZba7MlsWcPY+Qz8iRDTekMVz4+46Qn12q21234",
                "info": {
                    "em_host": self.em_host,
                    "em_port": int(self.em_port),
                    "em_wait_seconds": 5,
                    "em_codec": "slin16",
                    "em_sample_rate": 16000,
                    "em_sample_width": 2,
                    "save_record": 1,
                    "save_format": "wav",
                    "save_sample_rate": 16000,
                    "save_bit_rate": 8,
                    "save_filename": f"CALLPY-20230615223858844427-druid-{self.room.druid}",
                    "save_concat_druid": "mixing",
                    "speech_recognition": 1,
                    "detection_autoresponse": 1,
                    "detection_voice_start": 1,
                    "detection_absolute_silence": 1
                }
            }
            status, data_response = await self.make_post_request(url, data, description='CREATE')
            if status == 200:
                self.log.info(f'data_response={data_response}')
                if 'ssrc' in data_response:
                    self.em_ssrc = data_response['ssrc']
                else:
                    self.log.error('Not found ssrc')
            else:
                self.log.error(f'status={data_response} and data={data_response}')
        except Exception as e:
            self.log.error(f'report_start_ms e={e}')
            self.log.exception(e)

    async def send_event_progress(self, trigger_tag: str):
        """
        This is an asynchronous function that reports the stop of an event manager.

        @return None
        """
        self.log.info('send_event_progress')
        statuses = self.room.tags_statuses.get(trigger_tag)
        if statuses is None:
            return

        event_time = statuses.get('Dial#PROGRESS').get('external_time')
        ssrc = await self.em_ssrc

        try:
            url = 'http://127.0.0.1:7005/events'
            data = {
                "event_name": "PROGRESS",
                "event_time": event_time,
                "druid": self.room.druid,
                "chan_id": self.chan_id,
                "send_time": datetime.now().isoformat(),
                "token": "NE1K0Vz4pPa9PRJ+JtAibBZba7MlsWcPY+Qz8iRDTekMVz4+46Qn12q21234",
                "info": {
                    "em_host": self.em_host,
                    "em_port": self.em_port,
                    "em_ssrc": ssrc
                }
            }

            status, data_response = await self.make_post_request(url, data, description='PROGRESS')
            if status == 200:
                self.log.info(f'data_response={data_response}')
            else:
                self.log.error(f'status={data_response} and data={data_response}')
        except Exception as e:
            self.log.error(f'report_stop_em e={e}')
            self.log.exception(e)

    async def send_event_answer(self, trigger_tag: str):
        """
        This is an asynchronous function that reports the stop of an event manager.

        @return None
        """
        self.log.info('send_event_answer')
        statuses = self.room.tags_statuses.get(trigger_tag)
        if statuses is None:
            return

        event_time = statuses.get('Dial#ANSWER').get('external_time')
        ssrc = await self.em_ssrc

        try:
            url = 'http://127.0.0.1:7005/events'
            data = {
                "event_name": "ANSWER",
                "event_time": event_time,
                "druid": self.room.druid,
                "chan_id": self.chan_id,
                "send_time": datetime.now().isoformat(),
                "token": "NE1K0Vz4pPa9PRJ+JtAibBZba7MlsWcPY+Qz8iRDTekMVz4+46Qn12q21234",
                "info": {
                    "em_host": self.em_host,
                    "em_port": self.em_port,
                    "em_ssrc": ssrc
                }
            }

            status, data_response = await self.make_post_request(url, data, description='ANSWER')
            if status == 200:
                self.log.info(f'data_response={data_response}')
            else:
                self.log.error(f'status={data_response} and data={data_response}')
        except Exception as e:
            self.log.error(f'report_stop_em e={e}')
            self.log.exception(e)

    async def send_event_destroy(self, trigger_tag: str):
        """
        This is an asynchronous function that reports the stop of an event manager.

        @return None
        """
        self.log.info('send_event_destroy')
        statuses = self.room.tags_statuses.get(trigger_tag)
        if statuses is None:
            return

        event_time = statuses.get('StasisEnd').get('external_time')
        ssrc = await self.em_ssrc

        try:
            url = 'http://127.0.0.1:7005/events'
            data = {
                "event_name": "DESTROY",
                "event_time": event_time,
                "druid": self.room.druid,
                "chan_id": self.chan_id,
                "send_time": datetime.now().isoformat(),
                "token": "NE1K0Vz4pPa9PRJ+JtAibBZba7MlsWcPY+Qz8iRDTekMVz4+46Qn12q21234",
                "info": {
                    "em_host": self.em_host,
                    "em_port": self.em_port,
                    "em_ssrc": ssrc
                }
            }

            status, data_response = await self.make_post_request(url, data, description='DESTROY')
            if status == 200:
                self.log.info(f'data_response={data_response}')
            else:
                self.log.error(f'status={data_response} and data={data_response}')
        except Exception as e:
            self.log.error(f'report_stop_em e={e}')
            self.log.exception(e)

    async def check_trigger_chan_funcs(self, debug_log: int = 0):
        """
        This is an asynchronous function that checks the trigger channel functions.
        @return None
        """
        if debug_log > 0:
            self.log.debug(f'{debug_log}')

        for trigger in self.chan_plan.triggers:
            if debug_log > 0:
                self.log.debug(f'trigger.trigger_tag={trigger.trigger_tag}'
                               f' trigger.active={trigger.active}'
                               f' trigger.action={trigger.action}'
                               f' trigger.func={trigger.func}'
                               f'debug_log = {debug_log}')
            if trigger.action == 'func' and trigger.active and trigger.func is not None:
                trigger_tag_statuses = self.room.tags_statuses.get(trigger.trigger_tag, [])

                if debug_log > 0:
                    self.log.debug(f'trigger_tag_statuses={trigger_tag_statuses} debug_log = {debug_log}')

                if trigger.trigger_status in trigger_tag_statuses:
                    trigger.active = False
                    if trigger.func == 'send_event_create':
                        self.log.info('send_event_create')
                        await self.send_event_create(trigger.trigger_tag)
                    elif trigger.func == 'send_event_progress':
                        self.log.info('send_event_progress')
                        await self.send_event_progress(trigger.trigger_tag)
                    elif trigger.func == 'send_event_answer':
                        self.log.info('send_event_answer')
                        await self.send_event_answer(trigger.trigger_tag)
                    elif trigger.func == 'send_event_destroy':
                        self.log.info('send_event_destroy')
                        await self.send_event_destroy(trigger.trigger_tag)
                    else:
                        self.log.info(f'no found func={trigger.func}')
                        pass

    async def start_chan(self):
        """
        This is an asynchronous function that starts ChanEmedia.

        @return None
        """
        self.log.info('start ChanEmedia')
        self.external_host = self.params.get('external_host')

        if self.external_host is None or len(self.external_host) == 0:
            error = f'Invalid external_host={self.external_host}'
            self.log.error(error)
            await self.add_status_chan('dialplan_error', value=error)
            await self.add_status_chan('stop')
        else:

            create_chan_response = await self.ari.create_emedia_chan(chan_id=self.chan_id,
                                                                     external_host=self.external_host)
            await self.add_status_chan('api_create_chan', value=str(create_chan_response.get('http_code')))

            if create_chan_response.get('http_code') in (http.client.OK, http.client.NO_CONTENT):
                await self.ari.subscription(event_source=f'channel:{self.chan_id}')
                chan2bridge_response = await self.ari.add_channel_to_bridge(bridge_id=self.bridge_id,
                                                                            chan_id=self.chan_id)
                await self.add_status_chan('api_chan2bridge', value=str(chan2bridge_response.get('http_code')))

            else:
                await self.add_status_chan('error_create_chan', value=str(create_chan_response.get('message')))
                await self.add_status_chan('stop')
