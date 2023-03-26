import asyncio
import json
import platform

from loguru import logger

from src.ari.ari import ARI
from src.config import Config
from src.dialer import Dialer
from src.dialplan import Dialplan
from src.lead import Lead

logger.add("src/logs/loguru.log", rotation="1 day")


async def alive(config):
    while config['alive']:
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

    dial_plans: {}
    queue_msg_asterisk = []
    queue_lead = []

    with open('/opt/scripts/callpy_nemo/src/dialplan_dialog.json', "r") as dial_plan_file:
        dial_plan = Dialplan(json.load(dial_plan_file))
        dial_plans = {'redir1_end8': dial_plan}

    with open('/opt/scripts/callpy_nemo/src/leads.json', "r") as lead_json:
        lead = Lead(json.load(lead_json))
        queue_lead.append(lead)

    ari = ARI(cfg.config, queue_msg_asterisk, 'anydict')
    await ari.connect()
    peers = await ari.get_peers()
    logger.info(f"Peers: {peers}")
    # subscribe = await ari.subscription('anydict')
    # logger.info(f"Subscribe: {subscribe}")

    dialer = Dialer(ari=ari,
                    config=cfg.config,
                    queue_msg_asterisk=queue_msg_asterisk,
                    queue_lead=queue_lead,
                    dial_plans=dial_plans)
    asyncio.create_task(dialer.start_dialer())
    asyncio.create_task(dialer.run_message_pump_for_rooms())

    await alive(cfg.config)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.debug(f"User aborted through keyboard")
