import asyncio

from src.chan import Chan


class ChanSnoop(Chan):
    """For work with Snoop channel (so far only spy)"""

    target_chan_tag: str = ''
    target_chan_id: str = ''

    async def start_chan(self):
        """
        This is an asynchronous function that starts a ChanSnoop.
        """
        self.log.info('start ChanSnoop')
        await asyncio.sleep(0.1)
        self.target_chan_tag = self.params.get('target_chan_tag')

        if self.target_chan_tag not in self.room.tags_statuses:
            error = f'For target_chan_tag={self.target_chan_tag} not found tag in tags_statuses'
            self.log.error(error)
            await self.add_status_chan('dialplan_error', value=error)
            await self.add_status_chan('stop')
        else:
            self.target_chan_id = f'{self.target_chan_tag}-call_id-{self.call_id}'

            create_chan_response = await self.asterisk_client.create_snoop_chan(target_chan_id=self.target_chan_id,
                                                                                snoop_id=self.chan_id)
            await self.add_status_chan('api_create_chan', value=str(create_chan_response.http_code))

            if create_chan_response.success:
                await self.asterisk_client.subscription(event_source=f'channel:{self.chan_id}')
                chan2bridge_response = await self.asterisk_client.add_channel_to_bridge(bridge_id=self.bridge_id,
                                                                                        chan_id=self.chan_id)
                await self.add_status_chan('api_chan2bridge', value=str(chan2bridge_response.http_code))
            else:
                await self.add_status_chan('error_create_chan', value=str(create_chan_response.message))
                await self.add_status_chan('stop')

    async def check_trigger_chan_funcs(self, debug_log: int = 0):
        pass
