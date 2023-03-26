import asyncio
import json

import websockets
from loguru import logger

from src.ari.api_handler import APIHandler


# "DeviceStateChanged",
# "PlaybackStarted",
# "PlaybackContinuing",
# "PlaybackFinished",
# "RecordingStarted",
# "RecordingFinished",
# "RecordingFailed",
# "ApplicationMoveFailed",
# "ApplicationReplaced",
# "BridgeCreated",
# "BridgeDestroyed",
# "BridgeMerged",
# "BridgeBlindTransfer",
# "BridgeAttendedTransfer",
# "BridgeVideoSourceChanged",
# "ChannelCreated",
# "ChannelDestroyed",
# "ChannelEnteredBridge",
# "ChannelLeftBridge",
# "ChannelStateChange",
# "ChannelDtmfReceived",
# "ChannelDialplan",
# "ChannelCallerId",
# "ChannelUserevent",
# "ChannelHangupRequest",
# "ChannelVarset",
# "ChannelTalkingStarted",
# "ChannelTalkingFinished",
# "ChannelHold",
# "ChannelUnhold",
# "ContactStatusChange",
# "EndpointStateChange",
# "Dial",
# "StasisEnd",
# "StasisStart",
# "TextMessageReceived",
# "ChannelConnectedLine",
# "PeerStatusChange"


class ARI(APIHandler):
    def __init__(self, config: dict, queue_msg_asterisk: list, app: str):
        self._config = config
        self._host = self._config['asterisk_host']
        self._port = self._config['asterisk_port']
        self._login = self._config['asterisk_login']
        self._password = self._config['asterisk_password']
        self._uri = f"ws://{self._host}:{self._port}/ari/events?api_key={self._login}:{self._password}&app={app}&subscibeAll=true"
        self._cnt_fail = 0
        self._queue_msg = queue_msg_asterisk
        super().__init__()

    async def append_msg_with_tag(self, msg):
        pass

    async def check_connect(self):
        logger.debug(f'ARI try connect ws://{self._host}:{self._port}')
        try:
            ws = await websockets.connect(self._uri)
            await ws.close()
        except (websockets.InvalidStatus, Exception) as exp:
            logger.error(f'Check asterisk address, port, login and password exp={exp}')
            self._cnt_fail += 1
            await asyncio.sleep(self._cnt_fail)
            await self.connect()

    async def connect(self):
        await self.check_connect()
        asyncio.create_task(self.infinity_listener())
        await asyncio.sleep(0.1)

    async def infinity_listener(self):
        logger.info('ARI ws created and infinite listener started')
        async for websocket in websockets.connect(self._uri):
            if not self._config['alive']:
                break
            try:
                msg = await websocket.recv()
                self._queue_msg.append(json.loads(msg))

                logger.debug(len(self._queue_msg))
                logger.debug(f'Event = {self._queue_msg[-1]}')
            except websockets.ConnectionClosed as e:
                logger.error(f'ConnectionClosed e={e}')
                continue
            except websockets.ConnectionClosedError as e:
                logger.error(f'ConnectionClosedError e={e}')
                continue
            except Exception as e:
                logger.error(f'Exception e={e}')

        if self._config['alive']:
            await self.connect()


if __name__ == "__main__":
    queue = []
    dict_config = {"asterisk_host": "127.0.0.1", "asterisk_port": "8088",
                   "asterisk_login": "asterisk", "asterisk_password": "asterisk"}
    a = ARI(dict_config, queue, 'test')
    asyncio.run(a.connect())
