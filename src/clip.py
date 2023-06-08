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
        self.params: dict = clip_plan.params
        self.clip_id = f'{self.tag}-id-{self.lead_id}'

        self.log = logger.bind(object_id=self.clip_id)
        asyncio.create_task(self.add_status_clip(clip_plan.status, value=self.clip_id))

    def __del__(self):
        self.log.debug('object has died')

    async def add_status_clip(self, new_status, value: str = ''):
        await self.room.add_tag_status(self.tag, new_status, value=value)

    async def start_clip(self):
        self.log.info('start clip')
        audio_name = self.params.get('audio_name', None)
        if audio_name is not None and len(audio_name) > 0:
            start_playback_response = await self.ari.start_playback(chan_id=self.chan_id,
                                                                    clip_id=self.clip_id,
                                                                    name_audio=f"sound:{audio_name}")

            await self.add_status_clip('api_start_playback', value=start_playback_response.get('http_code'))
        else:
            await self.add_status_clip('error_in_audio_name')

    async def stop_clip(self):
        self.log.info('stop_clip')
        stop_playback_response = await self.ari.stop_playback(clip_id=self.clip_id)
        await self.add_status_clip('api_stop_playback', value=stop_playback_response.get('http_code'))
