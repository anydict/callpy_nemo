import asyncio

from src.chan import Chan
import http.client


class ChanOutbound(Chan):

    async def start_chan(self):
        self.log.info('start ChanOutbound')
        if self.tag == 'specialist':
            create_chan_response = await self.ari.create_chan(chan_id=self.chan_id,
                                                              endpoint='SIP/asterisk_extapi-1/321',
                                                              callerid='321')
        else:
            create_chan_response = await self.ari.create_chan(chan_id=self.chan_id,
                                                              endpoint='SIP/asterisk_extapi-1/123',
                                                              callerid='123')
        if create_chan_response.get('http_code') in (http.client.OK, http.client.NO_CONTENT):
            await self.ari.subscription(event_source=f'channel:{self.chan_id}')
            chan2bridge_response = await self.ari.add_channel_to_bridge(bridge_id=self.bridge_id,
                                                                        chan_id=self.chan_id)
            self.log.info(chan2bridge_response)

            dial_chan_response = await self.ari.dial_chan(chan_id=self.chan_id)
            self.log.info(dial_chan_response)

        else:
            await self.add_status_chan('api_error', create_chan_response.get('message'))
            await self.add_status_chan('stop')
