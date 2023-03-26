import asyncio
from datetime import datetime

from loguru import logger

from src.ari.ari import ARI
from src.bridge import Bridge
from src.dialplan import Dialplan
from src.lead import Lead


class Room(object):
    bridges: list[Bridge] = []
    queue_msg_room = []
    tags_statuses = {}

    # {
    #     "room":
    #         {
    #             "init": "2023-03-26T17:29:32.360",
    #             "ready": "2023-03-26T17:29:33.360"
    #         },
    #     "bridge_main":
    #         {
    #             "init": "2023-03-26T17:29:32.360",
    #             "ready": "2023-03-26T17:29:33.360"
    #         }
    # }

    def __init__(self, ari: ARI, config: dict, lead: Lead, dial_plan: Dialplan):
        self.ari = ari
        self.config = config
        self.lead_id = lead.lead_id
        self.lead = lead
        self.tag = dial_plan.tag
        self.dial_plan: Dialplan = dial_plan
        self.bridges_plan: list[Dialplan] = self.dial_plan.content
        self.room_id = f'{self.tag}{lead.lead_id}'
        self.add_status_room(dial_plan.status)

    def add_status_room(self, new_status):
        if self.tag not in self.tags_statuses:
            self.tags_statuses[self.tag] = {}
        self.tags_statuses[self.tag][new_status] = datetime.now().isoformat()

    async def append_queue_msg_room(self, msg: dict):
        self.queue_msg_room.append(msg)
        await asyncio.sleep(0)

    async def start_room(self):
        logger.info('start_dialer')
        self.add_status_room('ready')
        self.add_status_room('test')
        await self.check_trigger_bridges()

        while self.config['alive']:
            await asyncio.sleep(5)

    async def check_trigger_bridges(self):
        for bridge_plan in self.bridges_plan:
            if bridge_plan.tag in [bridge.tag for bridge in self.bridges]:
                continue
            if bridge_plan.trigger_tag in self.tags_statuses:
                bridge_status = self.tags_statuses.get(bridge_plan.trigger_tag)
                if bridge_plan.trigger_status in bridge_status:
                    bridge = Bridge(ari=self.ari,
                                    config=self.config,
                                    lead_id=self.lead_id,
                                    bridge_plan=bridge_plan,
                                    tags_statuses=self.tags_statuses)
                    self.bridges.append(bridge)
                    await bridge.start_bridge()

    async def run_room_message_pump(self):
        logger.info('run_message_pump_for_bridges')
        while self.config['alive']:
            if len(self.queue_msg_room) == 0:
                logger.debug(f'tags_statuses={self.tags_statuses}')
                await asyncio.sleep(5)
                continue

            msg = self.queue_msg_room.pop()

            for bridge in self.bridges:
                if 1 == 1:
                    await bridge.append_queue_msg_bridge(msg)

            logger.debug(f'run_room_message_pump msg={msg}')
            logger.debug(f'st={self.tags_statuses} phone={self.lead.phone}')
