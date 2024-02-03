from src.chan import Chan


class ChanInbound(Chan):
    """
    This is a class that inherits from Chan and is used to work with Inbound channels.

    """

    async def start_chan(self):
        """
        This is an asynchronous function that starts a channel.

        @return None
        """
        self.log.info('start ChanInbound')
        if self.tag == 'oper':
            create_chan_response = await self.asterisk_client.create_chan(chan_id=self.chan_id,
                                                                          endpoint='SIP/asterisk_extapi-1/321',
                                                                          callerid='321')
        else:
            create_chan_response = await self.asterisk_client.create_chan(chan_id=self.chan_id,
                                                                          endpoint='SIP/asterisk_extapi-1/123',
                                                                          callerid='123')
        if create_chan_response.success:
            await self.asterisk_client.subscription(event_source=f'channel:{self.chan_id}')
            chan2bridge_response = await self.asterisk_client.add_channel_to_bridge(bridge_id=self.bridge_id,
                                                                                    chan_id=self.chan_id)
            self.log.info(chan2bridge_response)

            dial_chan_response = await self.asterisk_client.dial_chan(chan_id=self.chan_id)
            self.log.info(dial_chan_response)

        else:
            await self.add_status_chan('api_error')
            await self.add_status_chan('stop')
