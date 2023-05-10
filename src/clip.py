import asyncio

from loguru import logger

from src.ari.ari import ARI
from src.config import Config
from src.dataclasses.dialplan import Dialplan


class Clip(object):
    """For work Playback on channel"""

    def __init__(self, ari: ARI, config: Config, room, clip_plan: Dialplan):
        self.ari = ari
        self.config = config
        self.room = room
        self.lead_id = room.lead_id
        self.clip_plan: list[Dialplan] = clip_plan.content
        self.tag = clip_plan.tag
        self.clip_id = f'{self.tag}-id-{self.lead_id}'

        self.log = logger.bind(object_id=self.clip_id)
        asyncio.create_task(self.add_status_clip(clip_plan.status))

    async def add_status_clip(self, new_status):
        await self.room.add_tag_status(self.tag, new_status)

    async def start_clip(self):
        await self.add_status_clip('ready')
        while self.config.alive:
            await asyncio.sleep(4)
