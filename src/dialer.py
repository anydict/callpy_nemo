import asyncio
from typing import Union

from loguru import logger

from src.ari.ari import ARI
from src.config import Config
from src.dataclasses.dialplan import Dialplan
from src.dataclasses.trigger_event import TriggerEvent
from src.lead import Lead
from src.room import Room


class Dialer(object):
    def __init__(self, config: Config, queue_lead: list[Lead], dial_plans: dict, app: str):
        self.ari: Union[ARI, None] = None
        self.config: Config = config
        self.queue_trigger_events: list[TriggerEvent] = []
        self.queue_lead: list = queue_lead
        self.dial_plans: dict = dial_plans
        self.app = app
        self.log = logger.bind(object_id='dialer')
        self.rooms = {}

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

            dial_plan = self.get_dial_plan('redir1_end8')
            lead = self.queue_lead.pop()
            room = Room(ari=self.ari, config=self.config, lead=lead, dial_plan=dial_plan)
            asyncio.create_task(room.start_room())
            self.rooms[lead.lead_id] = room

    async def run_message_pump_for_rooms(self):
        self.log.info('run_message_pump_for_rooms')
        while self.config.alive:
            if len(self.queue_trigger_events) == 0:
                await asyncio.sleep(0.1)
                continue

            event = self.queue_trigger_events.pop()
            self.log.info('FAVFAV')
            self.log.info(event)

            if event.lead_id in self.rooms:
                room: Room = self.rooms[event.lead_id]
                await room.trigger_event_handler(event)

    def get_dial_plan(self, name: str) -> Dialplan:
        return self.dial_plans[name]
