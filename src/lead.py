import re


class Lead(object):
    def __init__(self, params: dict):
        self.lead_id: str = str(params.get('lead_id', ''))
        self.phone: str = str(params.get('phone', ''))
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

    def check_params(self):
        if re.match(r"^[^0-9]+$", self.phone) or len(self.phone) == 0:
            raise RuntimeError(f'incorrect format phone={self.phone}')

        if len(self.phone_prefix) > 0 and re.match(r"^[^0-9]+$", self.phone_prefix):
            raise RuntimeError(f'incorrect format phone_prefix={self.phone_prefix}')

        if len(self.callerid) > 0 and re.match(r"^[^0-9]+$", self.callerid):
            raise RuntimeError(f'incorrect format callerid={self.callerid}')

        if len(self.callerid_ext) > 0 and re.match(r"^[^0-9]+$", self.callerid_ext):
            raise RuntimeError(f'incorrect format callerid_ext={self.callerid_ext}')
