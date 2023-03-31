import asyncio
import json

import websockets
from loguru import logger

from src.ari.api_handler import APIHandler
from src.config import Config
from src.dataclasses.trigger_event import TriggerEvent

status_equal_event_type = {
    'PlaybackStarted': 'ready',
    'PlaybackFinished': 'finish',
    'BridgeCreated': 'ready',
    'BridgeDestroyed': 'stop',
    'ChannelCreated': 'ready',
    'ChannelDestroyed': 'stop',
    'ChannelDtmfReceived': {'1': 'dtmf_1', '2': 'dtmf_2', '3': 'dtmf_3',
                            '4': 'dtmf_4', '5': 'dtmf_5', '6': 'dtmf_6',
                            '7': 'dtmf_7', '8': 'dtmf_8', '9': 'dtmf_9'},
    'ChannelVarset': 'rtp_stat',
    'StasisStart': 'start',
    'StasisEnd': 'stop',
}


class ARI(APIHandler):
    def __init__(self, config: Config, queue_msg_asterisk: list[TriggerEvent], app: str):
        self._config = config
        self._host = config.asterisk_host
        self._port = config.asterisk_port
        self._login = config.asterisk_login
        self._password = config.asterisk_password
        self._app = app

        # &subscribeAll=true
        # await self.ari.subscription()
        self._uri = f"ws://{self._host}:{self._port}/ari/events?api_key={self._login}:{self._password}&app={app}&subscribeAll=true"
        self._cnt_fail = 0
        self._queue_msg = queue_msg_asterisk
        self.log = logger.bind(object_id=f'ARI-{app}')
        super().__init__(self._host, self._port, self._login, self._password, self._app)

    async def append_msg_with_tag(self, msg):
        if 'type' in msg and msg['type'] in status_equal_event_type:
            self.log.debug(msg)
            if msg['type'] == 'ChannelDtmfReceived':
                status = status_equal_event_type[msg['type']].get(msg['digit'], 'dtmf_unknown')
            else:
                status = status_equal_event_type[msg['type']]

            tag = 'unknown'
            lead_id = 0
            if msg['type'] in ['ChannelCreated', 'ChannelDestroyed']:
                if '-id-' in msg['channel']['id']:
                    tag = str(msg['channel']['id']).split('-id-')[0]
                    lead_id = str(msg['channel']['id']).split('-id-')[1]
                else:
                    return

            if msg['type'] in ['ChannelVarset'] and msg['variable'] == 'STASISSTATUS':
                if '-id-' in msg['channel']['id']:
                    tag = str(msg['channel']['id']).split('-id-')[0]
                    lead_id = str(msg['channel']['id']).split('-id-')[1]

            t1 = TriggerEvent(app=self._app, tag=tag,
                              lead_id=lead_id, status=status,
                              msg='test', asterisk_time=msg['timestamp'])
            self._queue_msg.append(t1)
        await asyncio.sleep(0)

    async def check_connect(self):
        self.log.debug(f'ARI try connect ws://{self._host}:{self._port}')
        try:
            ws = await websockets.connect(self._uri)
            await ws.close()
        except (websockets.InvalidStatus, Exception) as e:
            self.log.error(f'Check asterisk address, port, login and password (e={e})')
            self._cnt_fail += 1
            await asyncio.sleep(self._cnt_fail)
            await self.connect()

    async def connect(self):
        await self.check_connect()
        asyncio.create_task(self.with_listener())
        await asyncio.sleep(0.4)

    async def with_listener(self):
        self.log.info('ARI ws created and infinite listener started')
        async with websockets.connect(self._uri) as ws:
            try:
                while self._config.alive:
                    msg = await ws.recv()
                    await self.append_msg_with_tag(json.loads(msg))
            except Exception as e:
                self.log.error(f'Exception')
                self.log.exception(e)

    async def infinity_listener(self):
        self.log.info('ARI ws created and infinite listener started')
        async for websocket in websockets.connect(self._uri):
            if not self._config.alive:
                break
            try:
                msg = await websocket.recv()
                await self.append_msg_with_tag(json.loads(msg))
            except websockets.ConnectionClosed as e:
                self.log.error(f'ConnectionClosed')
                self.log.exception(e)
                continue
            except websockets.ConnectionClosedError as e:
                self.log.error(f'ConnectionClosedError')
                self.log.exception(e)
                continue
            except Exception as e:
                self.log.error(f'Exception')
                self.log.exception(e)

        if self._config.alive:
            await self.connect()


if __name__ == "__main__":
    async def alive(ari):
        asyncio.create_task(ari.connect())
        while True:
            logger.info(f"alive")
            await asyncio.sleep(60)


    queue = []
    dict_config = {"asterisk_host": "127.0.0.1", "asterisk_port": "8088",
                   "asterisk_login": "asterisk", "asterisk_password": "asterisk"}
    conf = Config(dict_config=dict_config)
    a = ARI(conf, queue, 'test')
    asyncio.run(alive(a))
