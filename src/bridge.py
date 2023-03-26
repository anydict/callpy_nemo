import asyncio
from datetime import datetime

from loguru import logger


class Bridge(object):
    chans: list = []
    queue_msg_bridge = []

    def __init__(self, lead_id, config, bridge_plan, tags_statuses):
        self.lead_id = lead_id
        self._config = config
        self.tags_statuses = tags_statuses
        self.chan_plan = bridge_plan['content']
        self.tag = bridge_plan['tag']
        self.add_status_bridge(bridge_plan['status'])
        pass

    def add_status_bridge(self, new_status):
        if self.tag not in self.tags_statuses:
            self.tags_statuses[self.tag] = {}
        self.tags_statuses[self.tag][new_status] = datetime.now().isoformat()

    async def append_queue_msg_bridge(self, msg: dict):
        self.queue_msg_bridge.append(msg)
        await asyncio.sleep(0)

    async def check_trigger_bridges(self):
        for chan_plan in self.chan_plan:
            if chan_plan['tag'] in [chan.tag for chan in self.chans]:
                continue
            if chan_plan['trigger_tag'] in self.tags_statuses:
                bridge_status = self.tags_statuses.get(chan_plan['trigger_tag'])
                if chan_plan['trigger_status'] in bridge_status:
                    # bridge = Chan(lead_id=self.lead_id, config=self._config, chan_plan=chan_plan)
                    # self.chans.append(bridge)
                    # bridge.start_bridge()
                    pass

    async def start_bridge(self):
        self.add_status_bridge('ready')
        while self._config['alive']:
            await asyncio.sleep(4)

    async def run_bridge_message_pump(self):
        logger.info('run_bridge_message_pump')
        while self._config['alive']:
            if len(self.queue_msg_bridge) == 0:
                await asyncio.sleep(0.1)
                continue

            msg = self.queue_msg_bridge.pop()

            logger.debug(f'run_room_message_pump msg={msg}')
