import asyncio

from loguru import logger

from src.ari.ari import ARI
from src.config import Config
from src.dataclasses.dialplan import Dialplan


class Clip(object):
    """For work Playback on channel"""

    def __init__(self, ari: ARI, config: Config, room, chan_id: str, clip_plan: Dialplan):
        self.ari = ari
        self.config = config
        self.room = room
        self.chan_id = chan_id
        self.lead_id = room.lead_id
        self.clip_plan: list[Dialplan] = clip_plan.content
        self.tag = clip_plan.tag
        self.clip_id = f'{self.tag}-id-{self.lead_id}'

        self.log = logger.bind(object_id=self.clip_id)
        asyncio.create_task(self.add_status_clip(clip_plan.status, value=self.clip_id))

    def __del__(self):
        self.log.debug('object has died')

    async def add_status_clip(self, new_status, value: str = ''):
        await self.room.add_tag_status(self.tag, new_status, value=value)

    async def start_clip(self):
        self.log.info('start clip')
        start_playback_response = await self.ari.start_playback(chan_id=self.chan_id,
                                                                clip_id=self.clip_id,
                                                                name_audio="sound:hello")

        self.log.info(start_playback_response)

        start_playback_response = await self.ari.start_playback(chan_id=self.chan_id,
                                                                clip_id=self.clip_id,
                                                                name_audio="sound:hello")

        self.log.info(start_playback_response)

        await self.add_status_clip('api_send')
