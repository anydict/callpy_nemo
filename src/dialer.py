import asyncio

from src.room import Room


class Dialer(object):
    queue_msg = []
    queue_lead = []
    rooms = []

    def __init__(self, queue_msg_asterisk: list, queue_lead: list):
        self.queue_msg = queue_msg_asterisk
        self.queue_lead = queue_lead

    async def start_dialer(self):
        while True:
            if len(self.queue_lead) == 0:
                await asyncio.sleep(0.1)
                continue

            lead = self.queue_lead.pop()
            room = Room()
            asyncio.create_task(room.start_room())
            self.rooms.append(room)

    async def send_message_in_room(self):
        pass
