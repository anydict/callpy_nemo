from dataclasses import dataclass, asdict
from uuid import uuid4


@dataclass
class ApiRequest(object):
    url: str
    method: str
    request: dict = None
    timeout: int = None
    correct_http_code: set = (200, 201, 204, 404)
    debug_log: bool = True
    attempts: int = 3
    api_id: str = None

    def __post_init__(self):
        self.api_id = uuid4().hex

    def __str__(self):
        dict_object = asdict(self)
        if len(str(self.request)) > 1000:
            dict_object['request'] = f"len={len(str(self.request))}"

        return str(dict_object)


if __name__ == "__main__":
    ar = ApiRequest(url='http://example.com', method='POST', request={"action": "test"})
    print(ar)
