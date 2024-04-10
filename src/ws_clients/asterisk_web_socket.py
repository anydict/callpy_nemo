import json
import time
from multiprocessing import Process, Queue, Event

import websockets
from loguru import logger
from websockets.sync.client import connect

from src.config import Config
from src.trigger_event_manager import QueueEventManager

DISABLED_ASTERISK_EVENT_TYPES = [
    "ChannelDialplan"
]

DISABLED_TRIGGER_EVENT_TYPES = [
    "ChannelVarset#SIPCALLID"
]


class AsteriskWebSocket(Process):
    def __init__(self, config: Config, queue_events: Queue, finish_event: Event):
        super().__init__()
        self.config: Config = config
        self.finish_event: Event = finish_event
        self.cnt_fail: int = 0
        self.trigger_event_manager = QueueEventManager(queue_events=queue_events)
        self.ws_address: str = f"ws://{config.asterisk_host}:{config.asterisk_port}" \
                               f"/ari/events?api_key={config.asterisk_login}:{config.asterisk_password}" \
                               f"&app={config.app}&subscribeAll=true"
        self.log = logger.bind(object_id=f'{self.__class__.__name__}-{config.app}')

    def start(self):
        # see function self.run()
        super().start()

    def run(self):
        while self.finish_event.is_set() is False:
            self.check_connect()
            self.start_listener()

    def check_connect(self):
        self.log.debug(f'ARI try connect ws://{self.config.asterisk_host}:{self.config.asterisk_port}')
        try:
            ws: websockets.sync.client = connect(self.ws_address)
            ws.close()
        except (websockets.InvalidStatus, Exception) as e:
            self.log.error(f'Check asterisk address, port, login and password (e={e})')
            self.cnt_fail += 1
            time.sleep(min(self.cnt_fail, 60))
            self.check_connect()

    def start_listener(self):
        self.log.success('ARI ws created and infinite listener started')
        try:
            with connect(self.ws_address) as ws:
                while self.finish_event.is_set() is False:
                    try:
                        event_json = ws.recv(timeout=1)
                    except TimeoutError:
                        continue
                    except KeyboardInterrupt:
                        break

                    if self.config.asterisk_ari_log:
                        event = json.loads(event_json)
                        self.log.debug(event)

                        trigger_event = self.trigger_event_manager.asterisk_event_to_trigger_event(event)
                        if trigger_event.event_type in DISABLED_ASTERISK_EVENT_TYPES:
                            self.log.info(f'skip  trigger event with type={trigger_event.event_type}')
                        elif trigger_event.status in DISABLED_TRIGGER_EVENT_TYPES:
                            self.log.info(f'skip trigger event with status={trigger_event.status}')
                        else:
                            self.trigger_event_manager.append_queue_trigger_events(trigger_event)
        except Exception as e:
            self.log.warning(f'end start_listener e={e}')

        if self.finish_event.is_set() is False:
            time.sleep(4)  # waiting, maybe it is a night restart
        else:
            self.log.success('Close WebSocket - finish_event is set')


if __name__ == "__main__":
    cfg_path = '../../config/config.json'
    cfg = Config(config_path=cfg_path)
    a = AsteriskWebSocket(config=cfg, queue_events=Queue(), finish_event=Event())
    a.start()
