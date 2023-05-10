import json

from fastapi import APIRouter

from src.config import Config
from src.dialer import Dialer
from fastapi.responses import Response

from src.lead import Lead
from pydantic import BaseModel


class Item(BaseModel):
    token: str
    cmd: str
    intphone: int
    extphone: int
    idclient: int
    dir: str
    calleridrule: str


class Routers(object):
    def __init__(self, config, dialer):
        self.config: Config = config
        self.dialer: Dialer = dialer

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
        json_str = json.dumps({"stats": "123", "alive": self.config.alive}, indent=4, default=str)

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
            for bridge in self.dialer.rooms[room].bridges:
                for chan in self.dialer.rooms[room].bridges[bridge].chans:
                    chans.append(chan.chan_id)

        json_str = json.dumps({"chans": chans}, indent=4, default=str)

        return Response(content=json_str, media_type='application/json')

    def originate(self, item: Item):
        json_str = json.dumps({
            "token": item.token,
            "intphone": item.intphone,
            "extphone": item.extphone,
            "idclient": item.idclient,
            "dir": dir,
            "calleridrule": item.calleridrule
        }, indent=4, default=str)

        lead = Lead({
            "phone_specialist": str(item.intphone),
            "phone_client": str(item.extphone)
        })

        self.dialer.queue_lead.append(lead)

        return Response(content=json_str, media_type='application/json')

    def extapi(self,
               token: str = '',
               cmd: str = '',
               intphone: int = '',
               extphone: int = '',
               idclient: int = 0,
               dir: str = 'int',
               calleridrule: str = 'pool'):
        json_str = json.dumps({
            "token": token,
            "cmd": cmd,
            "intphone": intphone,
            "extphone": extphone,
            "idclient": idclient,
            "dir": dir,
            "calleridrule": calleridrule
        }, indent=4, default=str)

        return Response(content=json_str, media_type='application/json')
