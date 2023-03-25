import asyncio
import platform

from loguru import logger

from src.ari.ari import ARI
from src.config import Config
from src.dialer import Dialer

logger.add("logs/loguru.log", rotation="1 day")


async def alive(cfg):
    while cfg.config['alive']:
        logger.info(f"alive")
        await asyncio.sleep(60)


async def main():
    cfg = Config('config.json')

    logger.info("=" * 40, "System Information", "=" * 40)
    uname = platform.uname()
    logger.info(f"System: {uname.system}")
    logger.info(f"Node Name: {uname.node}")
    logger.info(f"Release: {uname.release}")
    logger.info(f"Machine: {uname.machine}")

    queue_msg_asterisk = []

    ari = ARI(cfg.config, queue_msg_asterisk, 'anydict')
    asyncio.create_task(ari.connect())

    dialer = Dialer(queue_msg_asterisk)
    asyncio.create_task(dialer.start_dialer())
    asyncio.create_task(dialer.start_dialer())

    await alive(cfg)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.debug(f"User aborted through keyboard")
