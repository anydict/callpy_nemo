from dataclasses import dataclass


# gate=dg
# dial_timeout=60
# phone_prefix=101
# phone_number=9237801235
# callerid=2020070101
# operator_id=1
# id_request=0

@dataclass
class DialOption(object):
    def __init__(self,
                 gate: str,
                 phone_string: str,
                 phone_prefix: str = '',
                 dial_timeout: int = 60,
                 callerid: str = '',
                 operator_id: int = 0,
                 id_request: int = 0):
        self.gate: str = gate
        self.dial_timeout: int = dial_timeout
        self.phone_prefix: str = phone_prefix
        self.phone_string: str = phone_string
        self.callerid: str = callerid
        self.operator_id: int = operator_id
        self.id_request: int = id_request
