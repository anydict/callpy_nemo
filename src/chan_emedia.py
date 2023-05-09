from src.chan import Chan
import http.client


class ChanEmedia(Chan):
    external_host: str = ''

    async def start_chan(self):
        self.log.info('start ChanEmedia')
        self.external_host = self.params.get('external_host')

        if self.external_host is None or len(self.external_host) == 0:
            self.log.error(f'Invalid external_host={self.external_host}')
        else:

            create_chan_response = await self.ari.create_emedia_chan(chan_id=self.chan_id,
                                                                     external_host=self.external_host)

            if create_chan_response.get('http_code') in (http.client.OK, http.client.NO_CONTENT):
                await self.ari.subscription(event_source=f'channel:{self.chan_id}')
                chan2bridge_response = await self.ari.add_channel_to_bridge(bridge_id=self.bridge_id,
                                                                            chan_id=self.chan_id)
                self.log.info(chan2bridge_response)

            else:
                await self.add_status_chan('api_error')
                await self.add_status_chan('stop')
