from dataclasses import dataclass


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
        """
        This is a constructor for a class that represents a phone call.

        @param gate - the gate to use for call
        @param phone_string - the phone number to call
        @param phone_prefix - the prefix to use for the phone number
        @param dial_timeout - the timeout for dialing the phone number
        @param callerid - the caller ID to use for call
        @param operator_id - the ID of the operator for call
        @param id_request - the ID of the request for call
        """
        self.gate: str = gate
        self.dial_timeout: int = dial_timeout
        self.phone_prefix: str = phone_prefix
        self.phone_string: str = phone_string
        self.callerid: str = callerid
        self.operator_id: int = operator_id
        self.id_request: int = id_request
