import datetime
import re
import uuid

from loguru import logger

from src.dataclasses.dial_option import DialOption


class Lead(object):
    """The data needed for the call"""

    def __init__(self, actionid: str, app: str, dialplan_name: str, system_prefix: str = 'TESTER'):
        self.druid: str = f'{app}:{uuid.uuid4().hex}'
        self.system_prefix = system_prefix
        self.actionid: str = self.get_actionid(actionid)  # id from external service
        self.dialplan_name: str = dialplan_name
        self.dial_options: dict[str, DialOption] = {}
        self.log = logger.bind(object_id=f'lead-{self.druid}')

    def __del__(self):
        self.log.debug('object has died')

    def get_actionid(self, actionid):
        if str(actionid) == '' or actionid is None:
            actionid = self.system_prefix + self.druid

        return actionid

    def add_dial_option_for_phone(self, option_name: str, phone: str, callerid: str = ''):

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
