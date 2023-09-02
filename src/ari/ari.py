import asyncio
import json

import websockets
from loguru import logger

from src.ari.api_handler import APIHandler
from src.config import Config
from src.trigger_event_manager import TriggerEventManager

DISABLED_ASTERISK_EVENT_TYPES = [
    "ChannelDialplan"
]

DISABLED_TRIGGER_EVENT_TYPES = [
    "ChannelVarset#SIPCALLID"
]


class ARI(APIHandler):
    def __init__(self, config: Config, trigger_event_manager: TriggerEventManager, app: str):
        self._config = config
        self._host = config.asterisk_host
        self._port = config.asterisk_port
        self._login = config.asterisk_login
        self._password = config.asterisk_password
        self._app = app
        self._uri = f"ws://{self._host}:{self._port}" \
                    f"/ari/events?api_key={self._login}:{self._password}&app={app}&subscribeAll=true"
        self._cnt_fail = 0
        self._trigger_event_manager = trigger_event_manager
        self.log = logger.bind(object_id=f'ARI-{app}')
        super().__init__(self._host, self._port, self._login, self._password, self._app)

    async def check_connect(self):
        self.log.debug(f'ARI try connect ws://{self._host}:{self._port}')
        try:
            ws = await websockets.connect(self._uri)
            await ws.close()
        except (websockets.InvalidStatus, Exception) as e:
            self.log.error(f'Check asterisk address, port, login and password (e={e})')
            self._cnt_fail += 1
            await asyncio.sleep(self._cnt_fail)
            await self.check_connect()

    async def connect(self):
        await self.check_connect()
        asyncio.create_task(self.with_listener())
        await asyncio.sleep(0.4)

    async def with_listener(self):
        self.log.info('ARI ws created and infinite listener started')
        async with websockets.connect(self._uri) as ws:
            try:
                while self._config.alive:
                    event_json = await ws.recv()
                    # self.log.debug(event_json)
                    try:
                        trigger_event = self._trigger_event_manager.asterisk_event_to_trigger_event(
                            json.loads(event_json))
                        if trigger_event.event_type in DISABLED_ASTERISK_EVENT_TYPES:
                            self.log.info(f'skip  trigger event with type={trigger_event.event_type}')
                        elif trigger_event.status in DISABLED_TRIGGER_EVENT_TYPES:
                            self.log.info(f'skip trigger event with status={trigger_event.status}')
                        else:
                            self._trigger_event_manager.append_queue_trigger_events(trigger_event)

                    except Exception as e:
                        self.log.exception(e)
            except Exception as e:
                self.log.error(f'Exception in with_listener (e={e})')

        # try reconnect
        if self._config.alive:
            asyncio.create_task(self.connect())


if __name__ == "__main__":
    async def alive(ari):
        asyncio.create_task(ari.connect())
        while True:
            logger.info(f"alive")
            await asyncio.sleep(60)


    tr_event_manager = TriggerEventManager()
    dict_config = {"asterisk_host": "127.0.0.1", "asterisk_port": "8088",
                   "asterisk_login": "asterisk", "asterisk_password": "asterisk"}
    conf = Config(join_config=dict_config)
    a = ARI(conf, tr_event_manager, 'test')
    asyncio.run(alive(a))
