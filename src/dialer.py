import asyncio

from loguru import logger

from src.ari.ari import ARI
from src.lead import Lead
from src.room import Room


class Dialer(object):
    queue_msg_asterisk = []
    queue_lead = []
    rooms = []

    def __init__(self, ari: ARI, config: dict, queue_msg_asterisk: list, queue_lead: list[Lead], dial_plans: dict):
        self.ari = ari
        self.config = config
        self.queue_msg_asterisk = queue_msg_asterisk
        self.queue_lead = queue_lead
        self.dial_plans = dial_plans

    async def start_dialer(self):
        logger.info('start_dialer')
        while self.config['alive']:
            if len(self.queue_lead) == 0:
                await asyncio.sleep(0.1)
                continue

            dial_plan = self.get_dial_plan('redir1_end8')
            room = Room(ari=self.ari, config=self.config, lead=self.queue_lead.pop(), dial_plan=dial_plan)
            asyncio.create_task(room.start_room())
            asyncio.create_task(room.run_room_message_pump())
            self.rooms.append(room)

    async def run_message_pump_for_rooms(self):
        logger.info('run_message_pump_for_rooms')
        while self.config['alive']:
            if len(self.queue_msg_asterisk) == 0:
                await asyncio.sleep(0.1)
                continue

            msg = self.queue_msg_asterisk.pop()
            for room in self.rooms:
                if 'type' in msg and msg['type'] == 'ChannelDialplan' and room.lead_id == msg['channel']['id']:
                    await room.append_queue_msg_room(msg)

    def get_dial_plan(self, name: str):
        return self.dial_plans[name]
