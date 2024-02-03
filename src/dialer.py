import asyncio
import json
import os
from datetime import datetime, timedelta
from multiprocessing import Event, Queue

from loguru import logger

from src.call import Call
from src.config import Config
from src.http_clients.http_asterisk_client import HttpAsteriskClient
from src.room import Room
from src.trigger_event_manager import QueueEventManager
from src.ws_clients.asterisk_web_socket import AsteriskWebSocket


class Dialer(object):
    """He runs calls and send messages in rooms"""

    def __init__(self, config: Config, app: str):
        self.config: Config = config
        self.queue_events: Queue = Queue()
        self.finish_event: Event = Event()
        self.trigger_event_manager = QueueEventManager(queue_events=self.queue_events)
        self.asterisk_client: HttpAsteriskClient = HttpAsteriskClient(config=config)
        self.call_queue: list[Call] = self.load_calls()
        self.raw_dialplans: dict = self.load_raw_dialplans()
        self.app = app
        self.log = logger.bind(object_id=self.__class__.__name__)
        self.rooms: dict[str, Room] = {}

    def __del__(self):
        self.log.debug('object has died')

    async def close_session(self):
        self.log.info('start close_session')
        self.finish_event.set()
        await self.asterisk_client.close_session()
        self.config.wait_shutdown = True
        self.log.info('end close_session')
        await asyncio.sleep(4)

    @staticmethod
    def load_raw_dialplans() -> dict:
        """
        Load the dialplans from two JSON files and return them as a dictionary.

        @return A dictionary containing the loaded dialplans.
        """
        raw_dialplans = {}
        with open('src/dialplans/dialplan_dialog.json', "r") as plan_file:
            raw_dialplans['redir1_end8'] = json.load(plan_file)

        with open('src/dialplans/dialplan_ivr.json', "r") as plan_file:
            raw_dialplans['oper_client'] = json.load(plan_file)

        return raw_dialplans

    @staticmethod
    def load_calls() -> list[Call]:
        """
        This function loads calls and returns them as a list of Call objects.

        @return A list of Call objects.
        """
        # with open('src/calls.json', "r") as json_content:
        #     call = Call(json.load(json_content))

        return []

    @staticmethod
    async def smart_sleep(delay: int):
        for _ in range(0, delay):
            await asyncio.sleep(delay)

    async def alive_report(self):
        """
        This is an asynchronous function that runs in the background
        And logs a message every 60 seconds while the `alive` flag is set to `True`.

        @return None
        """
        while self.config.alive:
            self.log.info(f"alive")
            await self.smart_sleep(60)

        self.log.info('end alive report')

    async def room_termination_handler(self):
        """
        This is an asynchronous function that runs in the background and checks rooms for terminated

        @return None
        """
        while self.config.alive:
            await self.smart_sleep(13)
            for call_id in list(self.rooms):
                try:
                    if self.rooms[call_id].check_tag_status('room', 'stop'):
                        time_stop = self.rooms[call_id].get_first_time_tag_status('room', 'stop')
                        if datetime.now() > datetime.fromisoformat(time_stop) + timedelta(seconds=10):
                            # wait 10 sec after stop status
                            # TODO add save db tags statuses
                            await self.rooms[call_id].bridge_termination_handler()
                            self.rooms.pop(call_id)
                            self.log.info(f'remove room with call_id={call_id} from memory')
                except Exception as e:
                    self.log.error(e)
                    self.log.exception(e)

    async def start_dialer(self):
        """
        This is an asynchronous function that starts a dialer.

        @return None
        """
        self.log.info('start_dialer')

        asterisk_web_socket: AsteriskWebSocket = AsteriskWebSocket(config=self.config,
                                                                   queue_events=self.queue_events,
                                                                   finish_event=self.finish_event)
        asterisk_web_socket.start()

        peers = await self.asterisk_client.get_peers()
        self.log.info(f"Peers: {peers}")

        asyncio.create_task(self.room_termination_handler())
        asyncio.create_task(self.run_message_pump_for_rooms())
        asyncio.create_task(self.alive_report())

        try:
            while self.config.wait_shutdown is False:
                await self.run_room_builder()
        except asyncio.CancelledError:
            self.log.warning('asyncio.CancelledError')

        self.log.info('start_dialer is end, go kill application')

        # close FastAPI and our application
        self.config.alive = False
        current_pid = os.getpid()
        os.kill(current_pid, 9)

    async def run_room_builder(self):
        # run new call until receive "restart" request (see api/routes.py)
        try:
            if len(self.call_queue) == 0:
                await asyncio.sleep(0.1)
                return

            call = self.call_queue.pop(0)  # get and remove first call from queue
            raw_dialplan = self.get_raw_dialplan(call.dialplan_name)

            if self.rooms.get(call.call_id) is not None:
                self.log.error(f'Room with call_id={call.call_id} already exists')
            else:
                self.log.info(f'Go create ROOM with dialplan_name={call.dialplan_name}')
                room = Room(asterisk_client=self.asterisk_client,
                            config=self.config,
                            call=call,
                            raw_dialplan=raw_dialplan,
                            app=self.app)
                asyncio.create_task(room.start_room())
                self.rooms[call.call_id] = room

        except Exception as e:
            self.log.exception(e)

    async def run_message_pump_for_rooms(self):
        """
        This is an asynchronous function that runs a message pump for rooms.

        @param self - the object instance
        @return None
        """
        self.log.info('run_message_pump_for_rooms')
        try:
            while self.config.wait_shutdown is False:
                event = self.trigger_event_manager.pop_first_queue_trigger_events()
                if event is None:
                    await asyncio.sleep(0.1)
                    continue

                self.log.debug(event)

                if event.call_id in self.rooms:
                    room: Room = self.rooms[event.call_id]
                    await room.trigger_event_handler(event)
        except Exception as e:
            self.log.error(e)

    def get_raw_dialplan(self, name: str) -> dict:
        """
        Given a name, return the raw dialplan associated with that name.

        @param name - the name of the dialplan
        @return the raw dialplan as a dictionary.
        """
        return self.raw_dialplans[name]
