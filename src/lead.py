import datetime
import re


class Lead(object):
    """The data needed for the call"""

    def __init__(self, params: dict):
        self.lead_id: str = self.get_lead_id(params)
        self.phone_specialist: str = str(params.get('phone_specialist', ''))
        self.phone_client: str = str(params.get('phone_client', ''))
        self.phone_prefix: str = str(params.get('phone_prefix', ''))
        self.callerid: str = str(params.get('callerid', ''))
        self.callerid_ext: str = str(params.get('callerid_ext', ''))
        self.team: str = str(params.get('team', ''))
        self.mobile: str = str(params.get('mobile', ''))
        self.provider: str = str(params.get('provider', ''))
        self.def_code: str = str(params.get('def_code', ''))
        self.operator_id: str = str(params.get('operator_id', ''))
        self.id_request: str = str(params.get('id_request', ''))
        # self.check_params()

    def get_lead_id(self, params):
        lead_id = str(params.get('lead_id', ''))
        if lead_id == '' or lead_id is None:
            lead_id = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')

        return lead_id

    def check_params(self):
        if re.match(r"^[^0-9]+$", self.phone_client) or len(self.phone_client) == 0:
            raise RuntimeError(f'incorrect format phone={self.phone_client}')

        if len(self.phone_prefix) > 0 and re.match(r"^[^0-9]+$", self.phone_prefix):
            raise RuntimeError(f'incorrect format phone_prefix={self.phone_prefix}')

        if len(self.callerid) > 0 and re.match(r"^[^0-9]+$", self.callerid):
            raise RuntimeError(f'incorrect format callerid={self.callerid}')

        if len(self.callerid_ext) > 0 and re.match(r"^[^0-9]+$", self.callerid_ext):
            raise RuntimeError(f'incorrect format callerid_ext={self.callerid_ext}')
