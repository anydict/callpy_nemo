import json
from datetime import datetime
from statistics import fmean

from fastapi import APIRouter, status
from fastapi.responses import Response
from loguru import logger
from pydantic import BaseModel, ValidationError
from starlette.responses import JSONResponse

from src.call import Call
from src.config import Config
from src.custom_dataclasses.trigger_event import TriggerEvent
from src.dialer import Dialer


class OriginateParams(BaseModel):
    token: str
    intphone: int
    extphone: int
    idclient: int
    dir: str
    calleridrule: str
    lead_id: int


class AnaliseParams(BaseModel):
    analise_name: str
    analise_time: str
    send_time: str
    token: str
    call_id: str
    info: dict


class HangupParams(BaseModel):
    token: str
    call_id: str


class Routers(object):
    def __init__(self, config, dialer):
        self.config: Config = config
        self.dialer: Dialer = dialer
        self.log = logger.bind(object_id=self.__class__.__name__)

        self.router = APIRouter(
            tags=["ALL"],
            responses={404: {"description": "Not found"}},
        )
        self.router.add_api_route(path="/", endpoint=self.get_root, methods=["GET"], tags=["Common"])
        self.router.add_api_route(path="/diag", endpoint=self.get_diag, methods=["GET"], tags=["Common"])
        self.router.add_api_route(path="/stats", endpoint=self.get_stats, methods=["GET"], tags=["Common"])

        self.router.add_api_route(path="/rooms", endpoint=self.get_rooms, methods=["GET"], tags=["Call"])
        self.router.add_api_route(path="/bridges", endpoint=self.get_bridges, methods=["GET"], tags=["Call"])
        self.router.add_api_route(path="/chans", endpoint=self.get_chans, methods=["GET"], tags=["Call"])
        self.router.add_api_route(path="/hangup", endpoint=self.hangup, methods=["DELETE"], tags=["Call"])

        self.router.add_api_route(path="/restart", endpoint=self.restart, methods=["POST"], tags=["Call"])
        self.router.add_api_route(path="/originate", endpoint=self.originate, methods=["POST"], tags=["Call"])

        self.router.add_api_route(path="/analise", endpoint=self.analise, methods=["POST"], tags=["MediaSonic"])

        # all the routes above are through this GET route
        self.router.add_api_route(path="/extapi", endpoint=self.extapi, methods=["GET"], tags=["ExtApi"])

    def get_root(self):
        json_str = json.dumps({"app": "callpy", "server": self.config.asterisk_host}, indent=4, default=str)

        return Response(content=json_str, media_type='application/json')

    def get_diag(self):
        json_str = json.dumps({
            "app": self.config.app,
            "wait_shutdown": self.config.wait_shutdown,
            "alive": self.config.alive,
        }, indent=4, default=str)

        return Response(content=json_str, media_type='application/json')

    def get_stats(self):
        stat_store = [0]
        for room in list(self.dialer.rooms.values()):
            for tag_status in list(room.tags_statuses.values()):
                if tag_status.get('external_time') != '':
                    d1 = datetime.strptime(tag_status.get('external_time'), '%Y-%m-%dT%H:%M:%S.%f')
                    d2 = datetime.strptime(tag_status.get('trigger_time'), '%Y-%m-%dT%H:%M:%S.%f')
                    diff = (d2 - d1).total_seconds()
                    stat_store.append(diff)
        json_str = json.dumps({
            "max": max(stat_store),
            "avg": fmean(stat_store),
            "alive": self.config.alive
        }, indent=4, default=str)

        return Response(content=json_str, media_type='application/json')

    def get_rooms(self):
        rooms = {}
        for room in self.dialer.rooms:
            rooms[self.dialer.rooms[room].room_id] = self.dialer.rooms[room].tags_statuses

        json_str = json.dumps({"rooms": rooms}, indent=4, default=str)

        return Response(content=json_str, media_type='application/json')

    def get_bridges(self):
        bridges = []
        for room in self.dialer.rooms:
            for bridge in self.dialer.rooms[room].bridges:
                bridges.append(self.dialer.rooms[room].bridges[bridge].bridge_id)

        json_str = json.dumps({"bridges": bridges}, indent=4, default=str)

        return Response(content=json_str, media_type='application/json')

    def get_chans(self):
        chans = []
        for room in self.dialer.rooms:
            for bridge in list(self.dialer.rooms[room].bridges.values()):
                for chan in list(bridge.chans.values()):
                    chans.append(chan)

        json_str = json.dumps({"chans": chans}, indent=4, default=str)

        return Response(content=json_str, media_type='application/json')

    def restart(self):
        self.config.wait_shutdown = True

        json_str = json.dumps({
            "app": self.config.app,
            "server": self.config.asterisk_host,
            "wait_shutdown": self.config.wait_shutdown,
            "alive": self.config.alive,
            "msg": "app restart started",
        }, indent=4, default=str)

        return Response(content=json_str, media_type='application/json')

    def originate(self, params: OriginateParams):
        if self.config.alive is False:
            return Response(status_code=503)

        call = Call(lead_id=params.lead_id,
                    dialplan_name='oper_client')
        call.add_dial_option_for_phone('extphone', phone=str(params.extphone), callerid=str(params.intphone))
        call.add_dial_option_for_phone('intphone', phone=str(params.intphone))

        for room in list(self.dialer.rooms.values()):
            if room.call.lead_id == params.lead_id:
                return Response(content='{"res": "ERROR", "msg": "such lead_id has already been launched"}',
                                media_type='application/json')

        self.dialer.call_queue.append(call)

        json_str = json.dumps({
            "token": params.token,
            "intphone": params.intphone,
            "extphone": params.extphone,
            "idclient": params.idclient,
            "dir": dir,
            "calleridrule": params.calleridrule,
            "call_id": call.call_id
        }, indent=4, default=str)

        return Response(content=json_str, media_type='application/json')

    def analise(self, params: AnaliseParams):
        if self.config.alive is False:
            return Response(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

        params.analise_name = params.analise_name.upper()

        if params.analise_name == 'START_ANALISE':
            pass
        elif params.analise_name == 'FIRST_BEEP_DETECT':
            pass
        elif params.analise_name == 'FIRST_NOISE_AFTER_ANSWER_DETECT':
            pass
        elif params.analise_name == 'FIRST_VOICE_DETECT':
            pass
        elif params.analise_name == 'AUTO_ANSWER_DETECT':
            pass
        elif params.analise_name == 'ABSOLUTE_SILENCE_DETECT':
            pass
        elif params.analise_name == 'VOICE_TO_TEXT':
            pass
        elif params.analise_name == 'END_ANALISE':
            pass

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"msg": "success"}
        )

    def hangup(self, params: HangupParams):
        json_str = json.dumps({
            "token": params.token,
            "call_id": params.call_id
        }, indent=4, default=str)

        for room in list(self.dialer.rooms.values()):
            if room.call_id == params.call_id:
                event = TriggerEvent(app=self.config.app,
                                     asterisk_id='',
                                     event_type='API_EVENT',
                                     external_time=datetime.now().isoformat(),
                                     trigger_time=datetime.now().isoformat(),
                                     delay=0,
                                     tag=room.tag,
                                     call_id=room.call_id,
                                     status='stop',
                                     value='api_hangup'
                                     )
                self.dialer.trigger_event_manager.append_queue_trigger_events(event)
                return Response(content=json_str, media_type='application/json')

        return Response(content='{"res": "ERROR", "msg": "Not found call_id"}', media_type='application/json')

    def extapi(self,
               token: str = '',
               cmd: str = '',
               intphone: int = '',
               extphone: int = '',
               idclient: int = 0,
               dir: str = 'int',  # noqa
               calleridrule: str = 'pool',
               lead_id: int = 0,
               call_id: str = ''
               ):
        json_str = json.dumps({
            "token": token,
            "cmd": cmd,
            "intphone": intphone,
            "extphone": extphone,
            "idclient": idclient,
            "dir": dir,
            "calleridrule": calleridrule,
            "lead_id": lead_id
        }, indent=4, default=str)

        # TODO add work with token
        if token != '612tkABC':
            return Response(content='{"res": "ERROR", "msg": "No valid token"}', media_type='application/json')

        if cmd == 'restart':
            return self.restart()
        elif cmd == 'originate':
            try:
                params = OriginateParams(token=token,
                                         intphone=intphone,
                                         extphone=extphone,
                                         idclient=idclient,
                                         dir=dir,
                                         calleridrule=calleridrule,
                                         lead_id=lead_id)
            except ValidationError as e:
                self.log.debug(f'ValidationError = {e} \n\n json_str = {json_str}')
                return Response(content='{"res": "ERROR", "msg": "Incorrect fields in request"}',
                                media_type='application/json')
            return self.originate(params)
        elif cmd == 'hangup':
            try:
                params = HangupParams(token=token,
                                      call_id=call_id)
            except ValidationError as e:
                self.log.debug(f'ValidationError = {e} \n\n json_str = {json_str}')
                return Response(content='{"res": "ERROR", "msg": "Incorrect fields in request"}',
                                media_type='application/json')
            return self.hangup(params)

        return Response(content=json_str, media_type='application/json')
