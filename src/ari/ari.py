import asyncio

import websockets
from loguru import logger


class ARI(object):
    def __init__(self, cfg: dict, queue_msg_asterisk: list, app: str):
        self._cfg = cfg
        self._host = self._cfg['asterisk_host']
        self._port = self._cfg['asterisk_port']
        self._login = self._cfg['asterisk_login']
        self._password = self._cfg['asterisk_password']
        self._uri = f"ws://{self._host}:{self._port}/ari/events?api_key={self._login}:{self._password}&app={app}"
        self._cnt_fail = 0
        self._queue_msg = queue_msg_asterisk

    async def connect(self):
        logger.debug(f'ARI try connect ws://{self._host}:{self._port}')
        try:
            ws = await websockets.connect(self._uri)
            await ws.close()
        except (websockets.InvalidStatus, Exception) as exp:
            logger.error(f'Check asterisk address, port, login and password exp={exp}')
            self._cnt_fail += 1
            await asyncio.sleep(self._cnt_fail)
            await self.connect()
        logger.info('ARI ws exist and infinite listener started')

        async for websocket in websockets.connect(self._uri):
            try:
                msg = await websocket.recv()
                self._queue_msg.append(msg)
                logger.debug(len(self._queue_msg))
            except websockets.ConnectionClosed as e:
                logger.error(f'ConnectionClosed e={e}')
                continue
            except websockets.ConnectionClosedError as e:
                logger.error(f'ConnectionClosedError e={e}')
                continue
            except Exception as e:
                logger.error(f'Exception e={e}')


if __name__ == "__main__":
    queue = []
    config = {"asterisk_host": "127.0.0.1", "asterisk_port": "8088",
              "asterisk_login": "asterisk", "asterisk_password": "asterisk"}
    q = ARI(config, queue, 'test')
    asyncio.run(q.connect())
