import datetime
import json
import re
from statistics import fmean

from fastapi import APIRouter
from loguru import logger

from src.config import Config
from src.dataclasses.trigger_event import TriggerEvent
from src.dialer import Dialer
from fastapi.responses import Response

from src.lead import Lead
from pydantic import BaseModel, ValidationError


class OriginateParams(BaseModel):
    token: str
    intphone: int
    extphone: int
    idclient: int
    dir: str
    calleridrule: str
    actionid: str | None


class HangupParams(BaseModel):
    token: str
    actionid: str


class Routers(object):
    def __init__(self, config, dialer):
        self.config: Config = config
        self.dialer: Dialer = dialer
        self.log = logger.bind(object_id='routers')

        self.router = APIRouter(
            tags=["ALL"],
            responses={404: {"description": "Not found"}},
        )
        self.router.add_api_route("/", self.get_root, methods=["GET"])
        self.router.add_api_route("/diag", self.get_diag, methods=["GET"])
        self.router.add_api_route("/stats", self.get_stats, methods=["GET"])
        self.router.add_api_route("/rooms", self.get_rooms, methods=["GET"])
        self.router.add_api_route("/rooms", self.get_rooms, methods=["GET"])
        self.router.add_api_route("/bridges", self.get_bridges, methods=["GET"])
        self.router.add_api_route("/chans", self.get_chans, methods=["GET"])
        self.router.add_api_route("/hangup", self.hangup, methods=["DELETE"])

        self.router.add_api_route("/restart", self.restart, methods=["POST"])
        self.router.add_api_route("/originate", self.originate, methods=["POST"], tags=["originate"])

        # all the routes above are through this GET route
        self.router.add_api_route("/extapi", self.extapi, methods=["GET"])

    def get_root(self):
        json_str = json.dumps({"app": "callpy", "server": self.config.asterisk_host}, indent=4, default=str)

        return Response(content=json_str, media_type='application/json')

    def get_diag(self):
        json_str = json.dumps({"res": "OK", "alive": self.config.alive}, indent=4, default=str)

        return Response(content=json_str, media_type='application/json')

    def get_stats(self):
        stat_store = [0]
        for room in self.dialer.rooms.values():
            for tag in room.tags_statuses:
                for status in room.tags_statuses[tag].values():
                    if status.get('external_time') != '':
                        d1 = datetime.datetime.strptime(status.get('external_time'),
                                                        '%Y-%m-%dT%H:%M:%S.%f')
                        d2 = datetime.datetime.strptime(status.get('trigger_time'),
                                                        '%Y-%m-%dT%H:%M:%S.%f')
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
            for bridge in self.dialer.rooms[room].bridges.values():
                for chan in bridge.chans.values():
                    chans.append(chan)

        json_str = json.dumps({"chans": chans}, indent=4, default=str)

        return Response(content=json_str, media_type='application/json')

    def restart(self):
        self.config.shutdown = True

        json_str = json.dumps({
            "app": self.config.app,
            "server": self.config.asterisk_host,
            "shutdown": self.config.shutdown,
            "alive": self.config.alive,
            "msg": "app restart started",
            "current_time": datetime.datetime.now().isoformat()
        }, indent=4, default=str)

        return Response(content=json_str, media_type='application/json')

    def originate(self, params: OriginateParams):
        if self.config.alive is False:
            return Response(status_code=503)

        system_prefix = re.findall('^[A-z]+', params.actionid)
        if len(system_prefix) == 0:
            system_prefix = 'TESTER'

        # lead = Lead(actionid=params.actionid,
        #             pp=self.config.app,
        #             dialplan_name='redir1_end8',
        #             system_prefix=system_prefix)
        lead = Lead(actionid=params.actionid,
                    app=self.config.app,
                    dialplan_name='specialist_client',
                    system_prefix=system_prefix)
        lead.add_dial_option_for_phone('extphone', phone=str(params.extphone), callerid=str(params.intphone))
        lead.add_dial_option_for_phone('intphone', phone=str(params.intphone))

        for room in self.dialer.rooms.values():
            if room.lead.actionid == params.actionid:
                return Response(content='{"res": "ERROR", "msg": "such actionid has already been launched"}',
                                media_type='application/json')

        self.dialer.queue_lead.append(lead)

        json_str = json.dumps({
            "token": params.token,
            "intphone": params.intphone,
            "extphone": params.extphone,
            "idclient": params.idclient,
            "dir": dir,
            "calleridrule": params.calleridrule,
            "actionid": lead.actionid
        }, indent=4, default=str)

        return Response(content=json_str, media_type='application/json')

    def hangup(self, params: HangupParams):
        json_str = json.dumps({
            "token": params.token,
            "actionid": params.actionid
        }, indent=4, default=str)

        for room in self.dialer.rooms.values():
            if room.lead.actionid == params.actionid:
                event = TriggerEvent({
                    "type": "ExternalEvent",
                    "druid": room.druid,
                    "tag": room.tag,
                    "status": "api_hangup",
                    "value": ""
                })
                self.dialer.queue_trigger_events.append(event)
                return Response(content=json_str, media_type='application/json')

        return Response(content='{"res": "ERROR", "msg": "Not found actionid"}', media_type='application/json')

    def extapi(self,
               token: str = '',
               cmd: str = '',
               intphone: int = '',
               extphone: int = '',
               idclient: int = 0,
               dir: str = 'int',  # noqa
               calleridrule: str = 'pool',
               actionid: str = ''
               ):
        json_str = json.dumps({
            "token": token,
            "cmd": cmd,
            "intphone": intphone,
            "extphone": extphone,
            "idclient": idclient,
            "dir": dir,
            "calleridrule": calleridrule,
            "actionid": actionid
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
                                         actionid=actionid)
            except ValidationError as e:
                self.log.debug(f'ValidationError = {e} \n\n json_str = {json_str}')
                return Response(content='{"res": "ERROR", "msg": "Incorrect fields in request"}',
                                media_type='application/json')
            return self.originate(params)
        elif cmd == 'hangup':
            try:
                params = HangupParams(token=token,
                                      actionid=actionid)
            except ValidationError as e:
                self.log.debug(f'ValidationError = {e} \n\n json_str = {json_str}')
                return Response(content='{"res": "ERROR", "msg": "Incorrect fields in request"}',
                                media_type='application/json')
            return self.hangup(params)

        return Response(content=json_str, media_type='application/json')
