import asyncio

from src.chan import Chan
import http.client


class ChanSnoop(Chan):
    """For work with Snoop channel (so far only spy)"""

    target_chan_tag: str = ''
    target_chan_id: str = ''

    async def start_chan(self):
        self.log.info('start ChanSnoop')
        await asyncio.sleep(0.1)
        self.target_chan_tag = self.params.get('target_chan_tag')

        if self.target_chan_tag not in self.room.tags_statuses:
            error = f'For target_chan_tag={self.target_chan_tag} not found tag in tags_statuses'
            self.log.error(error)
            await self.add_status_chan('dialplan_error', value=error)
            await self.add_status_chan('stop')
        else:
            self.target_chan_id = f'{self.target_chan_tag}-id-{self.druid}'

            create_chan_response = await self.ari.create_snoop_chan(target_chan_id=self.target_chan_id,
                                                                    snoop_id=self.chan_id)
            await self.add_status_chan('api_create_chan', value=str(create_chan_response.get('http_code')))

            if create_chan_response.get('http_code') in (http.client.OK, http.client.NO_CONTENT):
                await self.ari.subscription(event_source=f'channel:{self.chan_id}')
                chan2bridge_response = await self.ari.add_channel_to_bridge(bridge_id=self.bridge_id,
                                                                            chan_id=self.chan_id)
                await self.add_status_chan('api_chan2bridge', value=str(chan2bridge_response.get('http_code')))
            else:
                await self.add_status_chan('error_create_chan', value=str(create_chan_response.get('message')))
                await self.add_status_chan('stop')
