from src.chan import Chan
import http.client

from src.dataclasses.dial_option import DialOption


class ChanOutbound(Chan):
    """For work with Outbound channel"""

    async def start_chan(self):
        self.log.info('start ChanOutbound')
        dial_option_name = self.params.get('dial_option_name', None)
        if dial_option_name not in self.room.lead.dial_options:
            error = f'No found dial_option_name={dial_option_name} in lead.dial_options'
            self.log.error(error)
            await self.add_status_chan('api_error', value=error)
            await self.add_status_chan('stop')
            return

        dial_option: DialOption = self.room.lead.dial_options[dial_option_name]
        endpoint = f'SIP/{dial_option.gate}/{dial_option.phone_prefix}{dial_option.phone_string}'

        create_chan_response = await self.ari.create_chan(chan_id=self.chan_id,
                                                          endpoint=endpoint,
                                                          callerid=dial_option.callerid)

        if create_chan_response.get('http_code') in (http.client.OK, http.client.NO_CONTENT):
            await self.ari.subscription(event_source=f'channel:{self.chan_id}')
            chan2bridge_response = await self.ari.add_channel_to_bridge(bridge_id=self.bridge_id,
                                                                        chan_id=self.chan_id)
            self.log.info(chan2bridge_response)

            dial_chan_response = await self.ari.dial_chan(chan_id=self.chan_id)
            self.log.info(dial_chan_response)

        else:
            await self.add_status_chan('api_error', value=create_chan_response.get('message'))
            await self.add_status_chan('stop')
