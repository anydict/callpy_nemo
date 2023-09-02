import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Union

from loguru import logger

from src.ari.ari import ARI
from src.config import Config
from src.lead import Lead
from src.room import Room
from src.trigger_event_manager import TriggerEventManager


class Dialer(object):
    """He runs calls and send messages in rooms"""

    def __init__(self, config: Config, app: str):
        self.ari: Union[ARI, None] = None
        self.config: Config = config
        self.trigger_event_manager = TriggerEventManager()
        self.queue_lead: list[Lead] = self.load_leads()
        self.raw_dialplans: dict = self.load_raw_dialplans()
        self.app = app
        self.log = logger.bind(object_id='dialer')
        self.rooms: dict[str, Room] = {}

    def __del__(self):
        self.log.debug('object has died')

    def close_session(self):
        self.log.info('start close_session')
        asyncio.create_task(self.ari.close_session())
        self.log.info('end close_session')

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
    def load_leads() -> list[Lead]:
        """
        This function loads leads and returns them as a list of Lead objects.

        @return A list of Lead objects.
        """
        # with open('src/leads.json', "r") as lead_json:
        #     lead = Lead(json.load(lead_json))

        return []

    async def alive(self):
        """
        This is an asynchronous function that runs in the background
        And logs a message every 60 seconds while the `alive` flag is set to `True`.

        @return None
        """
        while self.config.alive:
            self.log.info(f"alive")
            await asyncio.sleep(60)

    async def room_termination_handler(self):
        """
        This is an asynchronous function that runs in the background and checks rooms for terminated

        @return None
        """
        while self.config.alive:
            await asyncio.sleep(10)
            for call_id in list(self.rooms):
                try:
                    if self.rooms[call_id].check_tag_status('room', 'stop'):
                        time_stop = self.rooms[call_id].get_first_time_tag_status('room', 'stop')
                        if datetime.now() + timedelta(seconds=30) < datetime.fromisoformat(time_stop):
                            # wait 30 sec after stop status
                            continue
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
        self.ari = ARI(self.config, self.trigger_event_manager, self.app)
        await self.ari.connect()

        peers = await self.ari.get_peers()
        subscribe = await self.ari.subscription()

        self.log.info(f"Peers: {peers}")
        self.log.info(f"Subscribe: {subscribe}")

        # run new call until receive "restart" request (see api/routes.py)
        while self.config.shutdown is False:
            if len(self.queue_lead) == 0:
                await asyncio.sleep(0.1)
                continue

            lead = self.queue_lead.pop(0)  # get and remove first lead from queue
            raw_dialplan = self.get_raw_dialplan(lead.dialplan_name)
            room_config = Config(self.config.join_config)  # Each room has its own Config

            if self.rooms.get(lead.call_id) is not None:
                self.log.error(f'Room with call_id={lead.call_id} already exists')
            else:
                room = Room(ari=self.ari, config=room_config, lead=lead, raw_dialplan=raw_dialplan, app=self.app)
                asyncio.create_task(room.start_room())
                self.rooms[lead.call_id] = room

        while len(list(self.rooms)) > 0:
            await asyncio.sleep(1)

        # full stop app
        self.config.alive = False
        # close FastAPI and our app
        parent_pid = os.getppid()
        current_pid = os.getpid()
        os.kill(parent_pid, 9)
        os.kill(current_pid, 9)

    async def run_message_pump_for_rooms(self):
        """
        This is an asynchronous function that runs a message pump for rooms.

        @param self - the object instance
        @return None
        """
        self.log.info('run_message_pump_for_rooms')
        while self.config.alive:
            if len(self.trigger_event_manager.queue_trigger_events) == 0:
                await asyncio.sleep(0.1)
                continue

            event = self.trigger_event_manager.pop_first_queue_trigger_events()  # get and remove first event
            self.log.debug(event)

            if event.call_id in self.rooms:
                room: Room = self.rooms[event.call_id]
                await room.trigger_event_handler(event)

    def get_raw_dialplan(self, name: str) -> dict:
        """
        Given a name, return the raw dialplan associated with that name.

        @param name - the name of the dialplan
        @return the raw dialplan as a dictionary.
        """
        return self.raw_dialplans[name]
