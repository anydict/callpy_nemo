import asyncio
from datetime import datetime

from loguru import logger

from src.ari.ari import ARI
from src.bridge import Bridge
from src.config import Config
from src.dataclasses.dialplan import Dialplan
from src.dataclasses.trigger_event import TriggerEvent
from src.lead import Lead


class Room(object):
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

    def __init__(self, ari: ARI, config: Config, lead: Lead, dial_plan: Dialplan):
        self.bridges: list[Bridge] = []
        self.queue_msg_room: list[TriggerEvent] = []
        self.tags_statuses = {}

        self.ari: ARI = ari
        self.config: Config = config
        self.lead_id: str = lead.lead_id
        self.lead: Lead = lead
        self.tag: str = dial_plan.tag
        self.room_plan: Dialplan = dial_plan
        self.bridges_plan: list[Dialplan] = self.room_plan.content
        self.room_id: str = f'{self.tag}-lead_id-{lead.lead_id}'

        self.log = logger.bind(object_id=self.room_id)
        asyncio.create_task(self.add_tag_status(tag=self.tag, new_status=dial_plan.status))

    async def add_tag_status(self, tag: str, new_status: str):
        self.log.info(f' tag={tag} new status={new_status} ')
        if tag not in self.tags_statuses:
            self.tags_statuses[tag] = {}
        self.tags_statuses[tag][new_status] = datetime.now().isoformat()
        await self.check_trigger_room()
        await self.check_trigger_bridges()
        await asyncio.sleep(0)

    async def append_queue_msg_room(self, msg: TriggerEvent):
        self.queue_msg_room.append(msg)
        await asyncio.sleep(0)

    async def start_room(self):
        self.log.info('start_room')
        await self.add_tag_status(tag=self.tag, new_status='ready')

        while self.config.alive:
            await asyncio.sleep(5)

    async def check_trigger_room(self):
        for trigger in [trg for trg in self.room_plan.triggers if trg.action == 'stop']:
            if trigger.trigger_status in self.tags_statuses.get(trigger.trigger_tag, []):
                self.log.info(f' need destroy')
                pass

    async def check_trigger_bridges(self):
        for bridge_plan in self.bridges_plan:

            if bridge_plan.tag in [bridge.tag for bridge in self.bridges]:
                for trigger in [trg for trg in bridge_plan.triggers if trg.action == 'stop']:
                    if trigger.trigger_status in self.tags_statuses.get(trigger.trigger_tag, []):
                        pass  # destroy bridge
            else:
                for trigger in [trg for trg in bridge_plan.triggers if trg.action == 'start']:
                    if trigger.trigger_status in self.tags_statuses.get(trigger.trigger_tag, []):
                        bridge = Bridge(ari=self.ari,
                                        config=self.config,
                                        room=self,
                                        bridge_plan=bridge_plan)
                        self.bridges.append(bridge)
                        asyncio.create_task(bridge.start_bridge())

        for bridge in self.bridges:
            await bridge.check_trigger_chans()

    async def run_room_message_pump(self):
        self.log.info('run_room_message_pump')
        while self.config.alive:
            if len(self.queue_msg_room) == 0:
                await asyncio.sleep(0.1)
                continue

            msg = self.queue_msg_room.pop()
            self.log.debug(f'msg={msg}')
