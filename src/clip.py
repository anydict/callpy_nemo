import asyncio

from loguru import logger

from src.config import Config
from src.custom_dataclasses.dialplan import Dialplan
from src.http_clients.http_asterisk_client import HttpAsteriskClient


class Clip(object):
    """For work Playback on channel"""

    def __init__(self, asterisk_client: HttpAsteriskClient, config: Config, room, chan_id: str, clip_plan: Dialplan):
        """
        This is a constructor for a class that initializes various instance variables.

        @param asterisk_client - HttpAsteriskClient object
        @param config - an instance of the Config class
        @param room - the room object
        @param chan_id - the channel ID
        @param clip_plan - an instance of the Dialplan class
        @return None
        """
        self.asterisk_client: HttpAsteriskClient = asterisk_client
        self.config: Config = config
        self.room = room
        self.chan_id: str = chan_id
        self.call_id: str = room.call_id
        self.clip_plan: Dialplan = clip_plan
        self.tag = clip_plan.tag
        self.params: dict = clip_plan.params
        self.clip_id = f'{self.tag}-call_id-{self.call_id}'

        self.log = logger.bind(object_id=self.clip_id)
        asyncio.create_task(self.add_status_clip(clip_plan.status, value=self.clip_id))

    def __del__(self):
        # DO NOT USE loguru here: https://github.com/Delgan/loguru/issues/712
        if self.config.console_log:
            print(f'{self.clip_id} object has died')

    async def add_status_clip(self, new_status, value: str = ''):
        """
        This is an asynchronous function that adds a new status clip to the room.

        @param self - the object instance
        @param new_status - the new status clip to be added
        @param value - the value of the new status clip
        @return None
        """
        asyncio.create_task(self.room.add_tag_status(self.tag, new_status, value=value))

    async def check_fully_playback(self):
        """
        This is an asynchronous function that checks if the playback of a video has finished.
        It checks the status of the tag in the room and returns True if the playback has finished successfully.

        @param self - the instance of the class
        @return True if the playback has finished successfully, False otherwise.
        """
        clip_statuses = self.room.tags_statuses.get(self.tag, [])
        if 'PlaybackFinished' not in clip_statuses:
            return False
        elif clip_statuses.get('PlaybackFinished').get('value') == 'failed':
            return False
        elif 'api_stop_playback' in clip_statuses:
            return False
        else:
            await self.add_status_clip('fully_playback', value='True')
            return True

    async def check_trigger_clip_funcs(self, debug_log):
        """
        This is an asynchronous function that checks the trigger clip functions.

        """
        if debug_log > 0:
            self.log.debug(f'debug_log={debug_log}')

        for trigger in self.clip_plan.triggers:
            if trigger.action != 'func' or trigger.func is None or trigger.active is False:
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
        media: str | list[str] = self.params.get('media', None)
        if media is not None and len(media) > 0:
            start_playback_response = await self.asterisk_client.start_chan_playback(chan_id=self.chan_id,
                                                                                     clip_id=self.clip_id,
                                                                                     media=f"{media}")

            await self.add_status_clip('api_start_playback', value=str(start_playback_response.http_code))
        else:
            self.log.error('Not found media for clip')
            await self.add_status_clip('error_in_audio_name')

    async def stop_clip(self):
        """
        This is an asynchronous function that stops the playback of a clip.
        It logs the action, stops the playback, and adds the status of the clip to the database.

        @return None
        """
        self.log.info('stop_clip')
        stop_playback_response = await self.asterisk_client.stop_playback(clip_id=self.clip_id)
        await self.add_status_clip('api_stop_playback', value=str(stop_playback_response.http_code))
