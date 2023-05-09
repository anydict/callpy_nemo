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
        self.bridges: dict[str, Bridge] = {}
        self.tags_statuses: dict[str, dict] = {}

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

    async def add_tag_status(self,
                             tag: str,
                             new_status: str,
                             asterisk_time: str = "",
                             trigger_time: str = "",
                             value: str = ""):
        self.log.info(f' tag={tag} new status={new_status} ')

        if tag not in self.tags_statuses:
            self.tags_statuses[tag] = {}

        if self.tags_statuses[tag].get(new_status) is None:
            self.tags_statuses[tag][new_status] = {
                "asterisk_time": asterisk_time,
                "trigger_time": trigger_time,
                "add_status_time": datetime.now().isoformat(),
                "value": value,
                "rewrite": []
            }
        else:
            row_rewrite = {
                "asterisk_time": asterisk_time,
                "trigger_time": trigger_time,
                "add_status_time": datetime.now().isoformat(),
                "value": value
            }
            self.tags_statuses[tag][new_status]["rewrite"].append(row_rewrite)

        await self.check_trigger_room()
        await self.check_trigger_bridges()
        self.log.info(self.tags_statuses)

        await asyncio.sleep(0)

    async def start_room(self):
        self.log.info('start_room')
        await self.add_tag_status(tag=self.tag, new_status='ready')

        while self.config.alive:
            await asyncio.sleep(5)

    async def check_trigger_room(self):
        for trigger in [trg for trg in self.room_plan.triggers if trg.action == 'terminate' and trg.active]:
            if trigger.trigger_status in self.tags_statuses.get(trigger.trigger_tag, []):
                trigger.active = False
                await self.add_tag_status(tag=self.tag, new_status='stop')

    async def check_trigger_bridges(self):

        for bridge_plan in self.bridges_plan:
            if bridge_plan.tag in [bridge.tag for bridge in self.bridges.values()]:
                # check terminate trigger if bridge already exist
                for trigger in [trg for trg in bridge_plan.triggers if trg.action == 'terminate' and trg.active]:
                    # check compliance the status of the object being monitored by the trigger
                    if trigger.trigger_status in self.tags_statuses.get(trigger.trigger_tag, []):
                        trigger.active = False
                        await self.bridges[bridge_plan.tag].destroy_bridge()
            else:
                # check start trigger if bridge does not exist
                for trigger in [trg for trg in bridge_plan.triggers if trg.action == 'start' and trg.active]:
                    if trigger.trigger_status in self.tags_statuses.get(trigger.trigger_tag, []):
                        trigger.active = False
                        bridge = Bridge(ari=self.ari,
                                        config=self.config,
                                        room=self,
                                        bridge_plan=bridge_plan)
                        self.bridges[bridge.tag] = bridge
                        asyncio.create_task(bridge.start_bridge())

        for bridge in self.bridges.values():
            await bridge.check_trigger_chans()

    async def trigger_event_handler(self, trigger_event: TriggerEvent):
        await self.add_tag_status(trigger_event.tag,
                                  trigger_event.status,
                                  trigger_event.asterisk_time,
                                  trigger_event.trigger_time,
                                  trigger_event.value)
