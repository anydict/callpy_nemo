import asyncio

from loguru import logger

from src.ari.ari import ARI
from src.clip import Clip
from src.config import Config
from src.dataclasses.dialplan import Dialplan


class Chan(object):
    """This class only for inheritance!"""
    clips: dict[str, Clip] = {}

    def __init__(self, ari: ARI, config: Config, room, bridge_id: str, chan_plan: Dialplan):
        """
        This is a constructor for a class that initializes various instance variables.

        @param ari - an instance of the ARI class
        @param config - an instance of the Config class
        @param room - the room object
        @param bridge_id - the ID of the bridge
        @param chan_plan - the dialplan for the channel
        @return None
        """
        self.ari = ari
        self.config = config
        self.room = room
        self.bridge_id = bridge_id
        self.druid = self.room.druid
        self.chan_plan = chan_plan
        self.clips_plan: list[Dialplan] = chan_plan.content
        self.tag = chan_plan.tag
        self.params: dict = chan_plan.params
        self.chan_id = f'{self.tag}-druid-{self.druid}'

        self.log = logger.bind(object_id=self.chan_id)
        asyncio.create_task(self.add_status_chan(chan_plan.status, value=self.chan_id))

    def __del__(self):
        """
        This is a destructor method for a class. It is called when the object is destroyed.
        It logs a debug message indicating that the object has died.

        @return None
        """
        self.log.debug('object has died')

    async def add_status_chan(self, new_status, value: str = ""):
        await self.room.add_tag_status(self.tag, new_status, value=value)

    async def clip_termination_handler(self):
        """
        This is an asynchronous function that handles the termination of a clip.
        If the configuration is still alive, it removes all clips from memory.

        @return None
        """
        if self.config.alive:
            clip_for_remove = []
            for clip_tag, clip in self.clips.items():
                clip_for_remove.append(clip_tag)

            for clip_tag in clip_for_remove:
                self.clips.pop(clip_tag)
                self.log.debug(f'remove clip with tag={clip_tag} from memory')
            del clip_for_remove

    async def check_trigger_clips(self):
        """
        This is an asynchronous function that checks for trigger clips.

        """
        for clip_plan in self.clips_plan:

            if clip_plan.tag in [clip.tag for clip in self.clips.values()]:
                # check terminate trigger if clip already exist
                for trigger in [trg for trg in clip_plan.triggers if trg.action == 'terminate' and trg.active]:
                    # check match the status of the object being monitored by the trigger
                    if trigger.trigger_status in self.room.tags_statuses.get(trigger.trigger_tag, []):
                        trigger.active = False
                        await self.clips[clip_plan.tag].stop_clip()
            else:
                # check start trigger if clip does not exist
                for trigger in [trg for trg in clip_plan.triggers if trg.action == 'start' and trg.active]:
                    if trigger.trigger_status in self.room.tags_statuses.get(trigger.trigger_tag, []):
                        trigger.active = False
                        clip = Clip(ari=self.ari,
                                    config=self.config,
                                    room=self.room,
                                    chan_id=self.chan_id,
                                    clip_plan=clip_plan)
                        self.clips[clip.tag] = clip
                        asyncio.create_task(clip.start_clip())
                        pass

        for clip in self.clips.values():
            await clip.check_trigger_clip_funcs()

    async def start_chan(self):
        """
        Implement your own function start_chan in inherited classes

        This is a base class method that is meant to be overridden by inherited classes.
        It raises an error message to remind the user that this method should not be called directly.

        @raises NotImplementedError - if the method is not implemented in the inherited class.
        """

        self.log.error('This class only for inheritance!')

    async def check_trigger_chan_funcs(self):
        """
        Implement your own function check_trigger_chan_funcs in inherited classes

        This is a placeholder function that is meant to be implemented in inherited classes.
        It is an asynchronous function that checks trigger channel functions.
        """
        pass
