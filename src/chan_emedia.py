import json
from datetime import datetime

from aiohttp import ClientConnectorError

from src.chan import Chan
import http.client
import aiohttp


class ChanEmedia(Chan):
    """For work with ExternalMedia channel"""

    external_host: str = ''
    asterisk_unicast_host: str = ''
    asterisk_unicast_port: int = 0

    async def make_get_request(self, url, params=None):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
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

    async def make_post_request(self, url, data=None):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as response:
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

    async def report_start_em(self):
        statuses = self.room.tags_statuses.get(self.tag)
        if statuses is None \
                or statuses.get('ChannelVarset#UNICASTRTP_LOCAL_ADDRESS') is None \
                or statuses.get('ChannelVarset#UNICASTRTP_LOCAL_PORT') is None:
            self.log.error(f'invalid statuses')
            self.log.error(statuses)
            return

        try:
            self.asterisk_unicast_host = statuses.get('ChannelVarset#UNICASTRTP_LOCAL_ADDRESS').get('value')
            self.asterisk_unicast_port = statuses.get('ChannelVarset#UNICASTRTP_LOCAL_PORT').get('value')
            url = 'https://127.0.0.1:1234/data'
            data = {
                'event': 'start_em',
                'chan_id': self.chan_id,
                'current_time': datetime.now().isoformat(),
                'params': {
                    'asterisk_unicast_host': self.asterisk_unicast_host,
                    'asterisk_unicast_port': self.asterisk_unicast_port,
                    'speech_recognition': 1,
                    'autoresponse_detection': 1,
                    'voice_start_detection': 1,
                    'silence_after_answer_detection': 1
                }
            }
            status, data_response = await self.make_post_request(url, data)
            if status == 200:
                self.log.info(f'data_response={data_response}')
            else:
                self.log.info(f'status={data_response} and data={data_response}')
        except Exception as e:
            self.log.error(f'report_start_ms e={e}')
            self.log.exception(e)

    async def report_stop_em(self):
        statuses = self.room.tags_statuses.get(self.tag)
        if statuses is None:
            return

        try:
            url = 'https://127.0.0.1:1234/data'
            data = {
                'event': 'start_em',
                'chan_id': self.chan_id,
                'current_time': datetime.now().isoformat(),
                'params': {}
            }
            status, data_response = await self.make_post_request(url, data)
            if status == 200:
                self.log.info(f'data_response={data_response}')
            else:
                self.log.info(f'status={data_response} and data={data_response}')
        except Exception as e:
            self.log.error(f'report_stop_em e={e}')
            self.log.exception(e)

    async def check_trigger_chan_funcs(self):
        for trigger in self.chan_plan.triggers:
            if trigger.action == 'func' and trigger.active and trigger.func is not None:

                if trigger.trigger_status in self.room.tags_statuses.get(trigger.trigger_tag, []):
                    trigger.active = False
                    if trigger.func == 'report_start_em':
                        self.log.info('report_start_em')
                        await self.report_start_em()
                    elif trigger.func == 'report_stop_em':
                        self.log.info('report_stop_em')
                        await self.report_stop_em()
                    else:
                        self.log.info(f'no found func={trigger.func}')
                        pass

    async def start_chan(self):
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
