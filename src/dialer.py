import asyncio
import json
from typing import Union

from loguru import logger

from src.ari.ari import ARI
from src.config import Config
from src.dataclasses.dialplan import Dialplan
from src.dataclasses.trigger_event import TriggerEvent
from src.lead import Lead
from src.room import Room


class Dialer(object):
    """He runs calls and send messages in rooms"""

    def __init__(self, config: Config, app: str):
        self.ari: Union[ARI, None] = None
        self.config: Config = config
        self.queue_trigger_events: list[TriggerEvent] = []
        self.queue_lead: list[Lead] = self.load_leads()
        self.raw_dialplans: dict = self.load_raw_dialplans()
        self.app = app
        self.log = logger.bind(object_id='dialer')
        self.rooms: dict[str, Room] = {}

    def __del__(self):
        self.log.debug('object has died')

    @staticmethod
    def load_raw_dialplans() -> dict:
        with open('src/dialplans/dialplan_dialog.json', "r") as plan_file:
            raw_dialplans = {'redir1_end8': json.load(plan_file)}

        return raw_dialplans

    @staticmethod
    def load_leads() -> list[Lead]:
        # with open('src/leads.json', "r") as lead_json:
        #     lead = Lead(json.load(lead_json))

        return []

    async def alive(self):
        while self.config.alive:
            self.log.info(f"alive")
            await asyncio.sleep(60)

    async def room_termination_handler(self):
        while self.config.alive:
            await asyncio.sleep(10)
            room_tags_for_remove = []
            for tag, room in self.rooms.items():
                if room.check_tag_status('room', 'stop'):
                    # TODO add save db tags statuses
                    await room.bridge_termination_handler()
                    room_tags_for_remove.append(tag)

            for room_tag in room_tags_for_remove:
                self.rooms.pop(room_tag)
                self.log.info(f'remove room with tag={room_tag} from memory')

    async def start_dialer(self):
        self.log.info('start_dialer')
        self.ari = ARI(self.config, self.queue_trigger_events, self.app)
        await self.ari.connect()

        peers = await self.ari.get_peers()
        subscribe = await self.ari.subscription()

        self.log.info(f"Peers: {peers}")
        self.log.info(f"Subscribe: {subscribe}")

        while self.config.alive:
            if len(self.queue_lead) == 0:
                await asyncio.sleep(0.1)
                continue

            raw_dialplan = self.get_raw_dialplan('redir1_end8')

            room_plan = Dialplan(raw_dialplan=raw_dialplan, app=self.app)  # Each room has its own Dialplan
            room_config = Config(self.config.join_config)  # Each room has its own Config

            lead = self.queue_lead.pop()
            if self.rooms.get(lead.lead_id) is not None:
                self.log.error(f'Room with lead_id={lead.lead_id} already exists')
            else:
                room = Room(ari=self.ari, config=room_config, lead=lead, room_plan=room_plan)
                asyncio.create_task(room.start_room())
                self.rooms[lead.lead_id] = room

    async def run_message_pump_for_rooms(self):
        self.log.info('run_message_pump_for_rooms')
        while self.config.alive:
            if len(self.queue_trigger_events) == 0:
                await asyncio.sleep(0.1)
                continue

            event = self.queue_trigger_events.pop(0)  # get and remove first event
            self.log.info(event)

            if event.lead_id in self.rooms:
                room: Room = self.rooms[event.lead_id]
                await room.trigger_event_handler(event)

    def get_raw_dialplan(self, name: str) -> dict:
        return self.raw_dialplans[name]
