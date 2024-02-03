import re

from src.chan import Chan
from src.custom_dataclasses.dial_option import DialOption


class ChanOutbound(Chan):
    """For work with Outbound channel"""

    async def get_sip_and_q850(self):
        """
        This is an asynchronous function that retrieves SIP and Q850 codes from a channel. 
        """
        if len(self.chan_name) > 0:
            get_hangupcause_response = await self.asterisk_client.get_chan_var(chan_id=self.chan_id,
                                                                               variable=f'HANGUPCAUSE')
            if get_hangupcause_response.success:
                hangupcause = get_hangupcause_response.result.get('value')
                await self.add_status_chan('q850', value=hangupcause)
            else:
                return

            get_sip_code_response = await self.asterisk_client.get_chan_var(
                chan_id=self.chan_id,
                variable=f'HANGUPCAUSE({self.chan_name},tech)'
            )
            if get_sip_code_response.success is False:
                return
            else:
                hangupcause_tech = get_sip_code_response.result.get('value')
                await self.add_status_chan('HANGUPCAUSE_TECH', value=hangupcause_tech)

            get_q850_code_response = await self.asterisk_client.get_chan_var(
                chan_id=self.chan_id,
                variable=f'HANGUPCAUSE({self.chan_name},ast)'
            )
            if get_q850_code_response.success:
                hangupcause_ast = get_q850_code_response.result.get('value')
                await self.add_status_chan('HANGUPCAUSE_AST', value=hangupcause_ast)

            sip_code = re.search(r'\d+', str(hangupcause_tech))
            if sip_code:
                await self.add_status_chan('sip_code', value=sip_code.group())

        else:
            self.log.warning('not found chan_name')

    async def check_trigger_chan_funcs(self, debug_log: int = 0):
        """
        This is an asynchronous function that checks the trigger channel functions.
        """
        for trigger in self.chan_plan.triggers:
            if trigger.action == 'func' and trigger.active and trigger.func is not None:

                if trigger.trigger_status in self.room.tags_statuses.get(trigger.trigger_tag, []):
                    trigger.active = False
                    if trigger.func == 'get_sip_and_q850':
                        self.log.info('get_sip_and_q850')
                        await self.get_sip_and_q850()
                    else:
                        self.log.info(f'no found func={trigger.func}')
                        pass

    async def start_chan(self):
        """
        This is an asynchronous function that starts a channel for outbound calls.

        @return None
        """
        self.log.info('start ChanOutbound')
        dial_option_name = self.params.get('dial_option_name', None)
        if dial_option_name not in self.room.call.dial_options:
            error = f'No found dial_option_name={dial_option_name} in call.dial_options'
            self.log.error(error)
            await self.add_status_chan('dialplan_error', value=error)
            await self.add_status_chan('stop')
            return

        dial_option: DialOption = self.room.call.dial_options[dial_option_name]
        endpoint = f'SIP/{dial_option.gate}/{dial_option.phone_prefix}{dial_option.phone_string}'

        create_chan_response = await self.asterisk_client.create_chan(chan_id=self.chan_id,
                                                                      endpoint=endpoint,
                                                                      callerid=dial_option.callerid)
        await self.add_status_chan('api_create_chan', value=str(create_chan_response.http_code))

        if create_chan_response.success:
            self.chan_name = create_chan_response.result.get('name')

            await self.asterisk_client.subscription(event_source=f'channel:{self.chan_id}')
            chan2bridge_response = await self.asterisk_client.add_channel_to_bridge(bridge_id=self.bridge_id,
                                                                                    chan_id=self.chan_id)
            if chan2bridge_response.success:
                self.log.info(chan2bridge_response)

                response_set_chan_var = await self.asterisk_client.set_chan_var(chan_id=self.chan_id,
                                                                                variable='CONNECTED(num)',
                                                                                value=dial_option.callerid)
                self.log.info(response_set_chan_var)

                dial_chan_response = await self.asterisk_client.dial_chan(chan_id=self.chan_id)
                await self.add_status_chan('api_dial_chan', value=str(dial_chan_response.http_code))
            else:
                self.log.warning(f'error in add chan to bridge, http_code={chan2bridge_response.http_code}')
                await self.asterisk_client.delete_chan(chan_id=self.chan_id, reason_code=21)

        else:
            await self.add_status_chan('error_create_chan', value=create_chan_response.message)
            await self.add_status_chan('stop')
