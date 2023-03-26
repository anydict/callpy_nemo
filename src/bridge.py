import asyncio
from datetime import datetime

from loguru import logger

from src.ari.ari import ARI
from src.chan import Chan
from src.dialplan import Dialplan


class Bridge(object):
    chans: list[Chan] = []
    queue_msg_bridge = []

    def __init__(self, ari: ARI, config: dict, lead_id: str, bridge_plan: Dialplan, tags_statuses):
        self.ari = ari
        self.config = config
        self.lead_id = lead_id
        self.tags_statuses = tags_statuses
        self.chan_plan: list[Dialplan] = bridge_plan.content
        self.tag = bridge_plan.tag
        self.bridge_id = f'{self.tag}#{lead_id}'
        self.add_status_bridge(bridge_plan.status)

    def add_status_bridge(self, new_status):
        if self.tag not in self.tags_statuses:
            self.tags_statuses[self.tag] = {}
        self.tags_statuses[self.tag][new_status] = datetime.now().isoformat()

    async def append_queue_msg_bridge(self, msg: dict):
        self.queue_msg_bridge.append(msg)
        await asyncio.sleep(0)

    async def check_trigger_chans(self):
        logger.info('check_trigger_chans')
        for chan_plan in self.chan_plan:
            if chan_plan.tag in [chan.tag for chan in self.chans]:
                continue
            if chan_plan.trigger_tag in self.tags_statuses:
                bridge_status = self.tags_statuses.get(chan_plan.trigger_tag)
                if chan_plan.trigger_status in bridge_status:
                    chan = Chan(ari=self.ari,
                                config=self.config,
                                lead_id=self.lead_id,
                                chan_plan=chan_plan,
                                tags_statuses=self.tags_statuses)
                    self.chans.append(chan)
                    asyncio.create_task(chan.start_chan())
        logger.info('check_trigger_chans end')

    async def start_bridge(self):
        try:
            logger.info('start_bridge')
            await self.ari.create_bridge(bridge_id=self.bridge_id)
            # await self.ari.subscription(app='anydict', event_source=f'bridge:{self.bridge_id}')
            self.add_status_bridge('ready')
            await self.check_trigger_chans()
            while self.config['alive']:
                logger.info('start_bridge alive')
                # await self.ari.custom_event('BridgeCreated', 'anydict')
                await asyncio.sleep(4)
        except Exception as e:
            logger.error(f'start_bridge e={e}')

    async def run_bridge_message_pump(self):
        logger.info('run_bridge_message_pump')
        while self.config['alive']:
            if len(self.queue_msg_bridge) == 0:
                await asyncio.sleep(0.1)
                continue

            msg = self.queue_msg_bridge.pop()

            for chan in self.chans:
                if 1 == 1:
                    await chan.append_queue_msg_chan(msg)

            logger.debug(f'run_room_message_pump msg={msg}')
