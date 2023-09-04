from dataclasses import dataclass


@dataclass
class AriResponse(object):
    def __init__(self,
                 http_code: int,
                 success: bool,
                 message: str,
                 json_content: dict):
        self.http_code: int = http_code
        self.success: bool = success
        self.message: str = message
        self.json_content: dict = json_content

    def __str__(self):
        return str({"http_code": self.http_code,
                    "success": self.success,
                    "message": self.message,
                    "json_content": self.json_content})
