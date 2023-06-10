import asyncio

from loguru import logger

from src.ari.ari import ARI
from src.config import Config
from src.dataclasses.dialplan import Dialplan


class Clip(object):
    """For work Playback on channel"""

    def __init__(self, ari: ARI, config: Config, room, chan_id: str, clip_plan: Dialplan):
        """
        This is a constructor for a class that initializes various instance variables.

        @param ari - an instance of the ARI class
        @param config - an instance of the Config class
        @param room - the room object
        @param chan_id - the channel ID
        @param clip_plan - an instance of the Dialplan class
        @return None
        """
        self.ari = ari
        self.config = config
        self.room = room
        self.chan_id = chan_id
        self.druid = room.druid
        self.clip_plan: Dialplan = clip_plan
        self.tag = clip_plan.tag
        self.params: dict = clip_plan.params
        self.clip_id = f'{self.tag}-druid-{self.druid}'

        self.log = logger.bind(object_id=self.clip_id)
        asyncio.create_task(self.add_status_clip(clip_plan.status, value=self.clip_id))

    def __del__(self):
        """
        This is a destructor method for a class. It is called when the object is destroyed.
        It logs a debug message indicating that the object has died.

        @return None
        """
        self.log.debug('object has died')

    async def add_status_clip(self, new_status, value: str = ''):
        """
        This is an asynchronous function that adds a new status clip to the room.

        @param self - the object instance
        @param new_status - the new status clip to be added
        @param value - the value of the new status clip
        @return None
        """
        await self.room.add_tag_status(self.tag, new_status, value=value)

    async def check_fully_playback(self):
        """
        This is an asynchronous function that checks if the playback of a video has finished.
        It checks the status of the tag in the room and returns True if the playback has finished successfully.

        @param self - the instance of the class
        @return True if the playback has finished successfully, False otherwise.
        """
        tag_statuses = self.room.tags_statuses.get(self.tag, [])
        if 'PlaybackFinished' not in tag_statuses:
            return False
        elif tag_statuses.get('PlaybackFinished').get('value') == 'failed':
            return False
        elif 'api_stop_playback' in self.room.tags_statuses.get(self.tag, []):
            return False
        else:
            await self.add_status_clip('fully_playback', value='True')
            return True

    async def check_trigger_clip_funcs(self):
        """
        This is an asynchronous function that checks the trigger clip functions.

        """
        for trigger in self.clip_plan.triggers:
            if trigger.action == 'func' and (trigger.func is None or trigger.action is False):
                continue

            if trigger.trigger_status in self.room.tags_statuses.get(trigger.trigger_tag, []):
                if trigger.func is None:
                    continue
                elif trigger.func == 'check_fully_playback':
                    trigger.active = False
                    await self.check_fully_playback()
                else:
                    self.log.info(f'no found func={trigger.func}')
                    continue

    async def start_clip(self):
        """
        This is an asynchronous function that starts a clip.
        If an audio name is provided, it starts playback of the audio.
        Otherwise, it adds an error status to the clip.

        @return None
        """
        self.log.info('start clip')
        audio_name = self.params.get('audio_name', None)
        if audio_name is not None and len(audio_name) > 0:
            start_playback_response = await self.ari.start_playback(chan_id=self.chan_id,
                                                                    clip_id=self.clip_id,
                                                                    name_audio=f"sound:{audio_name}")

            await self.add_status_clip('api_start_playback', value=str(start_playback_response.get('http_code')))
        else:
            await self.add_status_clip('error_in_audio_name')

    async def stop_clip(self):
        """
        This is an asynchronous function that stops the playback of a clip.
        It logs the action, stops the playback, and adds the status of the clip to the database.

        @return None
        """
        self.log.info('stop_clip')
        stop_playback_response = await self.ari.stop_playback(clip_id=self.clip_id)
        await self.add_status_clip('api_stop_playback', value=str(stop_playback_response.get('http_code')))
