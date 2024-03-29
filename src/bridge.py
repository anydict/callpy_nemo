import asyncio
from typing import Union

from loguru import logger

from src.chan_emedia import ChanEmedia
from src.chan_inbound import ChanInbound
from src.chan_outbound import ChanOutbound
from src.chan_snoop import ChanSnoop
from src.config import Config
from src.custom_dataclasses.dialplan import Dialplan
from src.http_clients.http_asterisk_client import HttpAsteriskClient


class Bridge(object):
    """He runs channels and check chans triggers"""

    def __init__(self, asterisk_client: HttpAsteriskClient, config: Config, room, bridge_plan: Dialplan):
        """
        This is a constructor for a class that initializes various instance variables.

        @param asterisk_client - HttpAsteriskClient object
        @param config - an instance of the Config class
        @param room - the room object
        @param bridge_plan - an instance of the Dialplan class
        @return None
        """
        self.asterisk_client: HttpAsteriskClient = asterisk_client
        self.config: Config = config
        self.room = room
        self.chans: dict[str, Union[ChanEmedia, ChanSnoop, ChanInbound, ChanOutbound]] = {}
        self.call_id: str = room.call_id
        self.bridge_plan: Dialplan = bridge_plan
        self.chan_plan: list[Dialplan] = bridge_plan.content
        self.tag = bridge_plan.tag
        self.bridge_id = f'{self.tag}-call_id-{self.call_id}'
        self.log = logger.bind(object_id=self.bridge_id)
        asyncio.create_task(self.add_status_bridge(bridge_plan.status, value=self.bridge_id))

    def __del__(self):
        # DO NOT USE loguru here: https://github.com/Delgan/loguru/issues/712
        if self.config.console_log:
            print(f'{self.bridge_id} object has died')

    async def add_status_bridge(self, new_status, value: str = ''):
        """
        This is an asynchronous function that adds a new status to a bridge.

        @param new_status - the new status to add to the bridge
        @param value - an optional value to associate with the new status
        @return None
        """
        asyncio.create_task(self.room.add_tag_status(self.tag, new_status=new_status, value=value))

    async def chan_termination_handler(self):
        """
        This is an asynchronous function that handles the termination of channels.

        @return None
        """
        if self.config.alive:
            for chan_tag in list(self.chans):
                await self.room.add_tag_status(tag=self.tag,
                                               new_status='stop',
                                               value='bridge_termination_handler')
                await self.chans[chan_tag].clip_termination_handler()
                self.chans.pop(chan_tag)
                self.log.debug(f'remove chan with tag={chan_tag} from memory')

    async def check_trigger_chans(self, debug_log: int = 0):
        """
        This is an asynchronous function that checks the trigger channels.

        @return None
        """
        if debug_log > 0:
            self.log.debug(f'debug_log={debug_log}')

        try:
            for chan_plan in self.chan_plan:
                for trigger in [trg for trg in chan_plan.triggers if trg.action == 'start' and trg.active]:
                    if trigger.trigger_status in self.room.tags_statuses.get(trigger.trigger_tag, []):
                        trigger.active = False
                        if chan_plan.type == 'chan_snoop':
                            chan = ChanSnoop(asterisk_client=self.asterisk_client,
                                             config=self.config,
                                             room=self.room,
                                             bridge_id=self.bridge_id,
                                             chan_plan=chan_plan)
                        elif chan_plan.type == 'chan_emedia':
                            chan = ChanEmedia(asterisk_client=self.asterisk_client,
                                              config=self.config,
                                              room=self.room,
                                              bridge_id=self.bridge_id,
                                              chan_plan=chan_plan)
                        elif chan_plan.type == 'chan_inbound':
                            chan = ChanInbound(asterisk_client=self.asterisk_client,
                                               config=self.config,
                                               room=self.room,
                                               bridge_id=self.bridge_id,
                                               chan_plan=chan_plan)
                        elif chan_plan.type == 'chan_outbound':
                            chan = ChanOutbound(asterisk_client=self.asterisk_client,
                                                config=self.config,
                                                room=self.room,
                                                bridge_id=self.bridge_id,
                                                chan_plan=chan_plan)
                        else:
                            logger.error(f'Invalid type for chan in (tag={chan_plan.tag}, type={chan_plan.type}')
                            logger.warning(f'Try use type=chan_outbound')
                            chan = ChanOutbound(asterisk_client=self.asterisk_client,
                                                config=self.config,
                                                room=self.room,
                                                bridge_id=self.bridge_id,
                                                chan_plan=chan_plan)
                        self.chans[chan.tag] = chan
                        asyncio.create_task(chan.start_chan())

        except Exception as e:
            self.log.exception(e)
            self.log.error(f'e={e}')

        for chan in list(self.chans.values()):
            if chan.call_id != self.call_id:
                self.log.error('WTF')
            await chan.check_trigger_clips(debug_log)
            await chan.check_trigger_chan_funcs(debug_log)

    async def start_bridge(self):
        """
        This is an asynchronous function that starts a bridge.

        @return None
        """
        self.log.info('start_bridge')
        if self.room.check_tag_status(tag='room', status='stop') is False:
            create_bridge_response = await self.asterisk_client.create_bridge(bridge_id=self.bridge_id)
            await self.add_status_bridge('api_create_bridge', value=str(create_bridge_response.http_code))

            if create_bridge_response.success:
                # Silence tone is necessary for the immediate transmission of RTP packets to the ExternalMedia channel
                await self.asterisk_client.start_bridge_playback(bridge_id=self.bridge_id,
                                                                 clip_id=f'silence_tone_{self.bridge_id}',
                                                                 media='tone:0')
            else:
                self.log.error(f'Problem when creating a bridge, msg={create_bridge_response.message}')
                await self.room.add_tag_status(tag=self.room.tag, new_status='stop', value='create_bridge_error')
                await self.add_status_bridge('create_bridge_error', value=create_bridge_response.message)

    async def destroy_bridge(self):
        """
        This is an asynchronous function that destroys a bridge and logs the event.
        It then adds the status of the bridge to the status list.

        @return None
        """
        self.log.info('destroy_bridge')
        destroy_bridge_response = await self.asterisk_client.destroy_bridge(bridge_id=self.bridge_id)
        await self.add_status_bridge('api_destroy_bridge', value=str(destroy_bridge_response.http_code))
