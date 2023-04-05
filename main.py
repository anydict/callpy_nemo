import asyncio
import json
import platform
import sys

from loguru import logger

from src.ari.ari import ARI
from src.config import Config
from src.dataclasses.dialplan import Dialplan
from src.dataclasses.trigger_event import TriggerEvent
from src.dialer import Dialer
from src.lead import Lead

logger.configure(extra={"object_id": "None"})  # Default values
logger.remove()

my_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> " \
            "<cyan>[{extra[object_id]}]</cyan>" \
            " [<level>{level}</level>] " \
            "<magenta>{name}</magenta>:<magenta>{function}</magenta>:<cyan>{line}</cyan>" \
            " - <level>{message}</level>"

# my_format = "{time} - [{extra[tag]}-id-{extra[lead_id]}] - {level} - {message}"
logger.add(sys.stdout, level="DEBUG", format=my_format, colorize=True)
logger.add("src/logs/callpy_nemo.log", rotation="1 day", format=my_format, )

logger = logger.bind(object_id='main')


async def alive(config: Config):
    while config.alive:
        logger.info(f"alive")
        await asyncio.sleep(60)


async def main():
    config = Config('config.json')

    logger.info("=" * 40, "System Information", "=" * 40)
    uname = platform.uname()
    logger.info(f"System: {uname.system}")
    logger.info(f"Node Name: {uname.node}")
    logger.info(f"Release: {uname.release}")
    logger.info(f"Machine: {uname.machine}")

    dial_plans: {}
    queue_msg_asterisk: list[TriggerEvent] = []
    queue_lead = []

    with open('src/dialplans/dialplan_dialog.json', "r") as dial_plan_file:
        dial_plan = Dialplan(params=json.load(dial_plan_file), app='anydict')
        dial_plans = {'redir1_end8': dial_plan}

    with open('src/leads.json', "r") as lead_json:
        lead = Lead(json.load(lead_json))
        queue_lead.append(lead)

    ari = ARI(config, queue_msg_asterisk, 'anydict')
    await ari.connect()
    peers = await ari.get_peers()
    logger.info(f"Peers: {peers}")
    subscribe = await ari.subscription()
    logger.info(f"Subscribe: {subscribe}")

    dialer = Dialer(ari=ari,
                    config=config,
                    queue_msg_asterisk=queue_msg_asterisk,
                    queue_lead=queue_lead,
                    dial_plans=dial_plans)
    asyncio.create_task(dialer.start_dialer())
    asyncio.create_task(dialer.run_message_pump_for_rooms())

    await alive(config)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.debug(f"User aborted through keyboard")
