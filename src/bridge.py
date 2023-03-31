import asyncio

from loguru import logger

from src.ari.ari import ARI
from src.chan import Chan
from src.config import Config
from src.dataclasses.dialplan import Dialplan


class Bridge(object):
    chans: list[Chan] = []

    def __init__(self, ari: ARI, config: Config, room, bridge_plan: Dialplan):
        self.ari = ari
        self.config = config
        self.room = room
        self.lead_id = room.lead_id
        self.bridge_plan: Dialplan = bridge_plan
        self.chan_plan: list[Dialplan] = bridge_plan.content
        self.tag = bridge_plan.tag
        self.bridge_id = f'{self.tag}-id-{self.lead_id}'
        self.log = logger.bind(object_id=self.bridge_id)
        asyncio.create_task(self.add_status_bridge(bridge_plan.status))

    def __del__(self):
        self.log.debug('object has died', lead_id=self.lead_id, tag=self.tag)

    async def add_status_bridge(self, new_status):
        await self.room.add_tag_status(self.tag, new_status)

    async def check_trigger_chans(self):
        try:
            for chan_plan in self.chan_plan:

                if chan_plan.tag in [chan.tag for chan in self.chans]:
                    continue

                for trigger in chan_plan.triggers:
                    if trigger.trigger_status in self.room.tags_statuses.get(trigger.trigger_tag, []):
                        chan = Chan(ari=self.ari,
                                    config=self.config,
                                    room=self.room,
                                    chan_plan=chan_plan)
                        self.chans.append(chan)
                        asyncio.create_task(chan.start_chan())
        except Exception as e:
            self.log.exception(e)

        for chan in self.chans:
            await chan.check_trigger_clips()

    async def start_bridge(self):
        try:
            self.log.info('start_bridge')
            await self.ari.create_bridge(bridge_id=self.bridge_id)
            await self.add_status_bridge('ready')
            while self.config.alive:
                # self.log.info('start_bridge alive')
                # await self.ari.custom_event('BridgeCreated', 'anydict')
                await asyncio.sleep(4)
        except Exception as e:
            self.log.exception(e)
