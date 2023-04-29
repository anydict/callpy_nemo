import asyncio

from loguru import logger

from src.ari.ari import ARI
from src.clip import Clip
from src.config import Config
from src.dataclasses.dialplan import Dialplan


class Chan(object):
    clips: list[Clip] = []

    def __init__(self, ari: ARI, config: Config, room, chan_plan: Dialplan):
        self.ari = ari
        self.config = config
        self.room = room
        self.lead_id = self.room.lead_id
        self.clips_plan: list[Dialplan] = chan_plan.content
        self.tag = chan_plan.tag
        self.chan_id = f'{self.tag}-id-{self.lead_id}'

        self.log = logger.bind(object_id=self.chan_id)
        asyncio.create_task(self.add_status_chan(chan_plan.status))

    async def add_status_chan(self, new_status):
        await self.room.add_tag_status(self.tag, new_status)

    async def check_trigger_clips(self):
        for clip_plan in self.clips_plan:

            if clip_plan.tag in [clip.tag for clip in self.clips]:
                continue

            for trigger in clip_plan.triggers:
                if trigger.trigger_status in self.room.tags_statuses.get(trigger.trigger_tag, []):
                    clip = Clip(ari=self.ari,
                                config=self.config,
                                room=self.room,
                                clip_plan=clip_plan)
                    self.clips.append(clip)
                    asyncio.create_task(clip.start_clip())
                    pass

    async def start_chan(self):
        self.log.info('start_chan')
        # await self.ari.create_chan(chan_id=self.chan_id, endpoint='SIP/client_phone/client_phone', callerid='123')
        api_response = await self.ari.create_chan(chan_id=self.chan_id, endpoint='SIP/asterisk_docker-1/123',
                                                  callerid='123')
        if api_response.get('http_code') == 200:
            await self.ari.subscription(event_source=f'channel:{self.chan_id}')
        else:
            await self.add_status_chan('api_error')
            await self.add_status_chan('stop')
        # while self.config.alive:
        #     await asyncio.sleep(4)
