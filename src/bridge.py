import asyncio
from typing import Union

from loguru import logger

from src.ari.ari import ARI
from src.chan_emedia import ChanEmedia
from src.chan_inbound import ChanInbound
from src.chan_outbound import ChanOutbound
from src.chan_snoop import ChanSnoop
from src.config import Config
from src.dataclasses.dialplan import Dialplan


class Bridge(object):
    """He runs channels and check chans triggers"""

    def __init__(self, ari: ARI, config: Config, room, bridge_plan: Dialplan):
        """
        This is a constructor for a class that initializes various instance variables.

        @param ari - an instance of the ARI class
        @param config - an instance of the Config class
        @param room - the room object
        @param bridge_plan - an instance of the Dialplan class
        @return None
        """
        self.ari = ari
        self.config = config
        self.room = room
        self.chans: dict[str, Union[ChanEmedia, ChanSnoop, ChanInbound, ChanOutbound]] = {}
        self.druid = room.druid
        self.bridge_plan: Dialplan = bridge_plan
        self.chan_plan: list[Dialplan] = bridge_plan.content
        self.tag = bridge_plan.tag
        self.bridge_id = f'{self.tag}-druid-{self.druid}'
        self.log = logger.bind(object_id=self.bridge_id)
        asyncio.create_task(self.add_status_bridge(bridge_plan.status, value=self.bridge_id))

    def __del__(self):
        """
        This is a destructor method for a class.
        It is called when the object is destroyed and logs a debug message indicating that the object has died.

        @return None
        """
        self.log.debug('object has died')

    async def add_status_bridge(self, new_status, value: str = ''):
        """
        This is an asynchronous function that adds a new status to a bridge.

        @param new_status - the new status to add to the bridge
        @param value - an optional value to associate with the new status
        @return None
        """
        await self.room.add_tag_status(self.tag, new_status=new_status, value=value)

    async def chan_termination_handler(self):
        """
        This is an asynchronous function that handles the termination of channels.

        @return None
        """
        if self.config.alive:
            for chan_tag in list(self.chans):
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
                            chan = ChanSnoop(ari=self.ari,
                                             config=self.config,
                                             room=self.room,
                                             bridge_id=self.bridge_id,
                                             chan_plan=chan_plan)
                        elif chan_plan.type == 'chan_emedia':
                            chan = ChanEmedia(ari=self.ari,
                                              config=self.config,
                                              room=self.room,
                                              bridge_id=self.bridge_id,
                                              chan_plan=chan_plan)
                        elif chan_plan.type == 'chan_inbound':
                            chan = ChanInbound(ari=self.ari,
                                               config=self.config,
                                               room=self.room,
                                               bridge_id=self.bridge_id,
                                               chan_plan=chan_plan)
                        elif chan_plan.type == 'chan_outbound':
                            chan = ChanOutbound(ari=self.ari,
                                                config=self.config,
                                                room=self.room,
                                                bridge_id=self.bridge_id,
                                                chan_plan=chan_plan)
                        else:
                            logger.error(f'Invalid type for chan in (tag={chan_plan.tag}, type={chan_plan.type}')
                            logger.warning(f'Try use type=chan_outbound')
                            chan = ChanOutbound(ari=self.ari,
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
            if chan.druid != self.druid:
                self.log.error('WTF')
            await chan.check_trigger_clips(debug_log)
            await chan.check_trigger_chan_funcs(debug_log)

    async def start_bridge(self):
        """
        This is an asynchronous function that starts a bridge.

        @return None
        """
        self.log.info('start_bridge')
        create_bridge_response = await self.ari.create_bridge(bridge_id=self.bridge_id)
        await self.add_status_bridge('api_create_bridge', value=str(create_bridge_response.get('http_code')))

    async def destroy_bridge(self):
        """
        This is an asynchronous function that destroys a bridge and logs the event.
        It then adds the status of the bridge to the status list.

        @return None
        """
        self.log.info('destroy_bridge')
        destroy_bridge_response = await self.ari.destroy_bridge(bridge_id=self.bridge_id)
        await self.add_status_bridge('api_destroy_bridge', value=str(destroy_bridge_response.get('http_code')))
