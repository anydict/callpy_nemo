import asyncio

from loguru import logger

from src.chan import Chan


class ChanOutbound(Chan):

    async def start_chan(self):
        logger.info('start_chan')
        self.add_status_chan('ready')
        # await self.check_trigger_chans()
        while self.config.alive:
            await asyncio.sleep(4)
