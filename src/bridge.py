import asyncio

from loguru import logger

from src.ari.ari import ARI
from src.chan import Chan
from src.chan_emedia import ChanEmedia
from src.chan_inbound import ChanInbound
from src.chan_outbound import ChanOutbound
from src.chan_snoop import ChanSnoop
from src.config import Config
from src.dataclasses.dialplan import Dialplan


class Bridge(object):
    """He runs channels and check chans triggers"""

    chans: dict[str, Chan] = {}

    def __init__(self, ari: ARI, config: Config, room, bridge_plan: Dialplan):
        self.ari = ari
        self.config = config
        self.room = room
        self.lead_id = room.lead_id
        self.bridge_plan: Dialplan = bridge_plan
        self.chan_plan: list[Dialplan] = bridge_plan.content
        self.tag = bridge_plan.tag
        self.bridge_id = f'{self.tag}-id-{self.lead_id}'
        self.log = logger.bind(object_id=self.bridge_id)
        asyncio.create_task(self.add_status_bridge(bridge_plan.status, value=self.bridge_id))

    def __del__(self):
        self.log.debug('object has died')

    async def add_status_bridge(self, new_status, value: str = ''):
        new_status = new_status.upper()  # precaution
        await self.room.add_tag_status(self.tag, new_status=new_status, value=value)

    async def chan_termination_handler(self):
        if self.config.alive:
            chan_for_remove = []
            for chan_tag, chan in self.chans.items():
                await chan.clip_termination_handler()
                chan_for_remove.append(chan_tag)

            for chan_tag in chan_for_remove:
                self.chans.pop(chan_tag)
                self.log.debug(f'remove chan with tag={chan_tag} from memory')
            del chan_for_remove

    async def check_trigger_chans(self):
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
                            logger.warning(f'Invalid type for chan in (tag={chan_plan.tag}, type={chan_plan.type}')
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

        for chan in self.chans.values():
            await chan.check_trigger_clips()

    async def start_bridge(self):
        self.log.info('start_bridge')
        await self.ari.create_bridge(bridge_id=self.bridge_id)
        await self.add_status_bridge('API_start')

    async def destroy_bridge(self):
        self.log.info('destroy_bridge')
        await self.ari.destroy_bridge(bridge_id=self.bridge_id)
