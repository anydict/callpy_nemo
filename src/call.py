from loguru import logger

from src.custom_dataclasses.dial_option import DialOption


class Call(object):
    """The data needed for the call"""

    def __init__(self,
                 lead_id: int,
                 dialplan_name: str):
        """
        This is a constructor for a class that represents a call.

        @param lead_id
        @param dialplan_name - a string representing the dialplan name
        @return None
        """
        self.lead_id: int = lead_id
        self.call_id: str = f'X{lead_id}'
        self.dialplan_name: str = dialplan_name
        self.dial_options: dict[str, DialOption] = {}
        self.log = logger.bind(object_id=f'{self.__class__.__name__}-{self.call_id}')

    def add_dial_option_for_phone(self, option_name: str, phone: str, callerid: str = ''):
        """
        This method adds a dial option for a phone number to the current instance of the class.

        @param option_name: The name of the option to add.
        @param phone: The phone number to add the option for.
        @param callerid: The caller ID to use for the call.
        @return None.
        """

        if len(phone) == 7:
            params = {
                "gate": 'asterisk_extapi-1',
                "dial_timeout": 50,
                "phone_prefix": "",
                "phone_string": phone,
                "callerid": callerid,
                "operator_id": 1,
                "id_request": 0
            }
        else:
            params = {
                "gate": 'asterisk_extapi-1',
                "dial_timeout": 50,
                "phone_prefix": "",
                "phone_string": phone,
                "callerid": "12345",
                "operator_id": 1,
                "id_request": 0
            }

        dial_option = DialOption(**params)
        self.dial_options[option_name] = dial_option

    # def check_params(self):
    #     if re.match(r"^[^0-9]+$", self.phone_client) or len(self.phone_client) == 0:
    #         raise RuntimeError(f' incorrect format phone={self.phone_client}')
    #
    #     if len(self.phone_prefix) > 0 and re.match(r"^[^0-9]+$", self.phone_prefix):
    #         raise RuntimeError(f' incorrect format phone_prefix={self.phone_prefix}')
    #
    #     if len(self.callerid) > 0 and re.match(r"^[^0-9]+$", self.callerid):
    #         raise RuntimeError(f' incorrect format callerid={self.callerid}')
    #
    #     if len(self.callerid_ext) > 0 and re.match(r"^[^0-9]+$", self.callerid_ext):
    #         raise RuntimeError(f' incorrect format callerid_ext={self.callerid_ext}')
