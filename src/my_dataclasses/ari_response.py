from dataclasses import dataclass


@dataclass
class AriResponse(object):
    http_code: int
    success: bool
    message: str
    json_content: dict
