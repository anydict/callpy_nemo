import asyncio
import platform
import sys

import uvicorn
from fastapi import FastAPI
from loguru import logger
from starlette.middleware.cors import CORSMiddleware

from src.api.routes import Routers
from src.config import Config
from src.dialer import Dialer

logger.configure(extra={"object_id": "None"})  # Default values if not bind extra variable
logger.remove()  # this removes duplicates in the console if we use custom log format

custom_log_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>  [<level>{level}</level>] " \
                    "<cyan>[{extra[object_id]}]</cyan>" \
                    "<magenta>{name}</magenta>:<magenta>{function}</magenta>:" \
                    "<cyan>{line}</cyan> - <level>{message}</level>"

# for console
logger.add(sink=sys.stdout,
           filter=lambda record: record["level"].name == record["level"].name,
           format=custom_log_format,
           colorize=True)
# different files for different message types
logger.add(sink="src/logs/debug.log",
           filter=lambda record: record["level"].name == "DEBUG",
           rotation="1 day",
           format=custom_log_format)
logger.add(sink="src/logs/error.log",
           filter=lambda record: record["level"].name == "ERROR",
           rotation="1 day",
           format=custom_log_format)
logger.add(sink="src/logs/callpy_nemo.log",
           filter=lambda record: record["level"].name not in ("DEBUG", "ERROR"),
           rotation="1 day",
           format=custom_log_format)

logger = logger.bind(object_id='main')

app = FastAPI()
config = Config('config.json')
dialer = Dialer(config=config, app='anydict')
routers = Routers(config=config, dialer=dialer)


@app.on_event('startup')
async def app_startup():
    # Run our application
    asyncio.create_task(dialer.start_dialer())
    asyncio.create_task(dialer.run_message_pump_for_rooms())
    asyncio.create_task(dialer.alive())


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8005"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(routers.router)

if __name__ == "__main__":
    try:
        logger.info("=" * 40, "System Information", "=" * 40)
        uname = platform.uname()
        logger.info(f"System: {uname.system}")
        logger.info(f"Node Name: {uname.node}")
        logger.info(f"Release: {uname.release}")
        logger.info(f"Machine: {uname.machine}")
        # Start fastapi and our application through on_event startup
        uvicorn.run("main:app", host='127.0.0.1', port=8005, log_level="info", reload=True)

        logger.info(f"Shutting down")
    except KeyboardInterrupt:
        logger.debug(f"User aborted through keyboard")
