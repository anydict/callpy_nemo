import asyncio

from loguru import logger

from src.ari.ari import ARI
from src.clip import Clip
from src.config import Config
from src.dataclasses.dialplan import Dialplan


class Chan(object):
    clips: list[Clip] = []

    def __init__(self, ari: ARI, config: Config, room, bridge_id: str, chan_plan: Dialplan):
        self.ari = ari
        self.config = config
        self.room = room
        self.bridge_id = bridge_id
        self.lead_id = self.room.lead_id
        self.clips_plan: list[Dialplan] = chan_plan.content
        self.tag = chan_plan.tag
        self.params: dict = chan_plan.params
        self.chan_id = f'{self.tag}-id-{self.lead_id}'

        self.log = logger.bind(object_id=self.chan_id)
        asyncio.create_task(self.add_status_chan(chan_plan.status))

    async def add_status_chan(self, new_status, value: str = ""):
        await self.room.add_tag_status(self.tag, new_status, value=value)

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
        if self.tag == 'specialist':
            create_chan_response = await self.ari.create_chan(chan_id=self.chan_id,
                                                              endpoint='SIP/asterisk_extapi-1/321',
                                                              callerid='321')
        else:
            create_chan_response = await self.ari.create_chan(chan_id=self.chan_id,
                                                              endpoint='SIP/asterisk_extapi-1/123',
                                                              callerid='123')
        if create_chan_response.get('http_code') == 200:
            await self.ari.subscription(event_source=f'channel:{self.chan_id}')
            chan2bridge_response = await self.ari.add_channel_to_bridge(bridge_id=self.bridge_id,
                                                                        chan_id=self.chan_id)
            self.log.info(chan2bridge_response)

            dial_chan_response = await self.ari.dial_chan(chan_id=self.chan_id)
            self.log.info(dial_chan_response)

        else:
            await self.add_status_chan('api_error', create_chan_response.get('message'))
            await self.add_status_chan('stop')
