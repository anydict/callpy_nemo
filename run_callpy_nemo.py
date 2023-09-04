import asyncio
import json
import os
import platform
import sys
import uuid

import uvicorn
from fastapi import FastAPI, Request, Depends
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from loguru import logger
from starlette.middleware.cors import CORSMiddleware

from src.api.routes import Routers
from src.config import Config
from src.dialer import Dialer

dialer = None


async def app_startup():
    """Run our application"""
    global dialer
    dialer = Dialer(config=config, app=config.app)
    routers = Routers(config=config, dialer=dialer)

    app.include_router(routers.router, dependencies=[Depends(logging_dependency)])

    asyncio.create_task(dialer.start_dialer())
    asyncio.create_task(dialer.room_termination_handler())
    asyncio.create_task(dialer.run_message_pump_for_rooms())
    asyncio.create_task(dialer.alive())


async def app_shutdown():
    if isinstance(dialer, Dialer):
        dialer.close_session()


async def logging_dependency(request: Request):
    uuid4_str = str(uuid.uuid4())
    logger.debug(f"uuid4_str={uuid4_str} {request.method} {request.url}")
    logger.debug(f"uuid4_str={uuid4_str} Params:")
    for name, value in request.path_params.items():
        logger.debug(f"uuid4_str={uuid4_str}\t{name}: {value}")
    logger.debug(f"uuid4_str={uuid4_str} Headers:")
    for name, value in request.headers.items():
        logger.debug(f"uuid4_str={uuid4_str}\t{name}: {value}")


async def custom_validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    logging validation error

    @param request:
    @param exc:
    @return:
    """
    errors = []
    for error in exc.errors():
        errors.append({
            'loc': error['loc'],
            'msg': error['msg'],
            'type': error['type']
        })
    logger.error(f"ValidationError in path: {request.url.path}")
    logger.error(f"ValidationError detail: {errors}")
    logger.error(request.headers)

    request_body = await request.body()
    logger.error(request_body)

    return await request_validation_exception_handler(request, exc)


if __name__ == "__main__":
    try:
        join_config = {}
        if os.path.isfile('config.json'):
            with open('config.json', "r") as jsonfile:
                join_config = json.load(jsonfile)

        config = Config(join_config=join_config)

        logger.configure(extra={"object_id": "None"})  # Default values if not bind extra variable
        logger.remove()  # this removes duplicates in the console if we use custom log format

        custom_log_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>[<level>{level}</level>]" \
                            "<cyan>[{extra[object_id]}]</cyan>" \
                            "<magenta>{name}</magenta>:<magenta>{function}</magenta>:" \
                            "<cyan>{line}</cyan> - <level>{message}</level>"

        # for console
        if config.log_console:
            logger.add(sink=sys.stdout,
                       filter=lambda record: record["level"].name == record["level"].name,
                       format=custom_log_format,
                       colorize=True)
        # different files for different message types
        logger.add(sink="logs/debug.log",
                   filter=lambda record: record["level"].name == "DEBUG",
                   rotation="1000 MB",
                   compression='gz',
                   format=custom_log_format)
        logger.add(sink="logs/error.log",
                   filter=lambda record: record["level"].name == "ERROR",
                   rotation="1000 MB",
                   compression='gz',
                   format=custom_log_format)
        logger.add(sink=f"logs/{config.app}.log",
                   filter=lambda record: record["level"].name not in ("DEBUG", "ERROR"),
                   rotation="1000 MB",
                   compression='gz',
                   format=custom_log_format)

        logger = logger.bind(object_id='main')

        app = FastAPI(exception_handlers={RequestValidationError: custom_validation_exception_handler})

        app.add_middleware(CORSMiddleware,
                           allow_origins=[f"http://{config.app_api_host}:{config.app_api_port}"],
                           allow_credentials=True,
                           allow_methods=["*"],
                           allow_headers=["*"])

        logger.info("=" * 40, "System Information", "=" * 40)
        uname = platform.uname()
        logger.info(f"System: {uname.system}")
        logger.info(f"Node Name: {uname.node}")
        logger.info(f"Release: {uname.release}")
        logger.info(f"Machine: {uname.machine}")
        logger.info(f"Parent pid: {os.getppid()}")
        logger.info(f"Current pid: {os.getpid()}")
        logger.info(f"API bind address: {config.app_api_host}:{config.app_api_port}")

        uvicorn_log_config = uvicorn.config.LOGGING_CONFIG
        del uvicorn_log_config["loggers"]

        # Start FastAPI and our application in app_startup
        app.add_event_handler('startup', app_startup)
        app.add_event_handler('shutdown', app_shutdown)
        uvicorn.run(app=f'__main__:app',
                    host=config.app_api_host,
                    port=config.app_api_port,
                    log_level="info",
                    log_config=uvicorn_log_config,
                    reload=False)

        logger.info(f"Shutting down")
    except KeyboardInterrupt:
        logger.debug(f"User aborted through keyboard")
    except Exception as e:
        logger.exception(e)
