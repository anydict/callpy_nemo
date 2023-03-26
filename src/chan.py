import asyncio
from datetime import datetime

from loguru import logger

from src.ari.ari import ARI
from src.dialplan import Dialplan


class Chan(object):
    clips = []
    queue_msg_chan = []

    def __init__(self, ari: ARI, config: dict, lead_id: str, chan_plan: Dialplan, tags_statuses):
        self.ari = ari
        self.config = config
        self.lead_id = lead_id
        self.tags_statuses = tags_statuses
        self.clip_plan: list[Dialplan] = chan_plan.content
        self.tag = chan_plan.tag
        self.chan_id = f'{self.tag}#{lead_id}'
        self.add_status_chan(chan_plan.status)

    def add_status_chan(self, new_status):
        if self.tag not in self.tags_statuses:
            self.tags_statuses[self.tag] = {}
        self.tags_statuses[self.tag][new_status] = datetime.now().isoformat()

    async def append_queue_msg_chan(self, msg: dict):
        self.queue_msg_chan.append(msg)
        await asyncio.sleep(0)

    async def check_trigger_clips(self):
        for clip_plan in self.clip_plan:
            if clip_plan.tag in [clip.tag for clip in self.clips]:
                continue
            if clip_plan.trigger_tag in self.tags_statuses:
                bridge_status = self.tags_statuses.get(clip_plan.trigger_tag)
                if clip_plan.trigger_status in bridge_status:
                    # self.chans.append(chan)
                    # chan.start_chan()
                    pass

    async def start_chan(self):
        self.add_status_chan('ready')
        await self.check_trigger_clips()
        while self.config['alive']:
            await asyncio.sleep(4)

    async def run_message_pump_for_chans(self):
        logger.info('run_message_pump_for_chans')
        while self.config['alive']:
            if len(self.queue_msg_chan) == 0:
                await asyncio.sleep(0.1)
                continue

            msg = self.queue_msg_chan.pop()

            for clip in self.clips:
                if 1 == 1:
                    await clip.append_queue_msg_bridge(msg)

            logger.debug(f'run_room_message_pump msg={msg}')
