import asyncio

from loguru import logger

from src.ari.ari import ARI
from src.clip import Clip
from src.config import Config
from src.dataclasses.dialplan import Dialplan


class Chan(object):
    """This class only for inheritance!"""
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
        asyncio.create_task(self.add_status_chan(chan_plan.status, value=self.chan_id))

    def __del__(self):
        self.log.debug('object has died')

    async def add_status_chan(self, new_status, value: str = ""):
        await self.room.add_tag_status(self.tag, new_status, value=value)

    async def clip_termination_handler(self):
        if self.config.alive:
            clip_for_remove = []
            for clip in self.clips:
                clip_for_remove.append(clip)

            for clip in clip_for_remove:
                self.clips.remove(clip)
                self.log.debug(f'remove clip with tag={clip.tag} from memory')
            del clip_for_remove

    async def check_trigger_clips(self):
        for clip_plan in self.clips_plan:

            if clip_plan.tag in [clip.tag for clip in self.clips]:
                continue

            for trigger in clip_plan.triggers:
                if trigger.trigger_status in self.room.tags_statuses.get(trigger.trigger_tag, []):
                    clip = Clip(ari=self.ari,
                                config=self.config,
                                room=self.room,
                                chan_id=self.chan_id,
                                clip_plan=clip_plan)
                    self.clips.append(clip)
                    asyncio.create_task(clip.start_clip())
                    pass

    async def start_chan(self):
        """Implement your own function start_chan in inherited classes"""

        self.log.error('This class only for inheritance!')
