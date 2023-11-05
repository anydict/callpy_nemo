import time

from aiohttp import client
from loguru import logger

from src.my_dataclasses.api_request import ApiRequest
from src.my_dataclasses.api_response import ApiResponse


class BaseClient(object):

    def __init__(self):
        self.client_session = client.ClientSession()
        self.log = logger.bind(object_id='BaseClient')

    async def close_session(self):
        if self.client_session:
            await self.client_session.close()

    async def send(self, api_request: ApiRequest) -> ApiResponse:
        start_time = time.time()
        api_response: ApiResponse = ApiResponse(http_code=0,
                                                execute_time=0,
                                                net_status=False,
                                                success=False,
                                                message='',
                                                result=None)

        for attempt in range(0, api_request.attempts):
            api_response.attempt = attempt
            if attempt > 0 or api_request.debug_log:
                self.log.info(f"BEFORE api_request={api_request}")
            try:
                async with self.client_session.request(method=api_request.method,
                                                       url=api_request.url,
                                                       json=api_request.request,
                                                       timeout=api_request.timeout) as response:
                    api_response.http_code = response.status
                    api_response.content_type = response.content_type
                    api_response.execute_time = time.time() - start_time
                    if api_request.correct_http_code in response.status:
                        pass
                    else:
                        pass

            except Exception as e:
                self.log.exception(e)
        return api_response
