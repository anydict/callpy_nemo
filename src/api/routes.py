from fastapi import APIRouter

from src.config import Config
from src.dialer import Dialer


class Routers(object):
    def __init__(self, config, dialer):
        self.config: Config = config
        self.dialer: Dialer = dialer

        self.router = APIRouter(
            tags=["diag"],
            responses={404: {"description": "Not found"}},
        )
        self.router.add_api_route("/", self.get_root, methods=["GET"])
        self.router.add_api_route("/diag", self.get_diag, methods=["GET"])
        self.router.add_api_route("/stats", self.get_stats, methods=["GET"])
        self.router.add_api_route("/rooms", self.get_rooms, methods=["GET"])
        self.router.add_api_route("/rooms", self.get_rooms, methods=["GET"])
        self.router.add_api_route("/bridges", self.get_bridges, methods=["GET"])
        self.router.add_api_route("/chans", self.get_chans, methods=["GET"])

    def get_root(self):
        return {"app": "callpy", "server": self.config.asterisk_host}

    def get_diag(self):
        return {"res": "OK", "alive": self.config.alive}

    def get_stats(self):
        return {"stats": "123", "alive": self.config.alive}

    def get_rooms(self):
        rooms = []
        for room in self.dialer.rooms:
            rooms.append(self.dialer.rooms[room].room_id)
        return {"rooms": rooms}

    def get_bridges(self):
        bridges = []
        for room in self.dialer.rooms:
            for bridge in self.dialer.rooms[room].bridges:
                bridges.append(self.dialer.rooms[room].bridges[bridge].bridge_id)
        return {"bridges": bridges}

    def get_chans(self):
        chans = []
        for room in self.dialer.rooms:
            for bridge in self.dialer.rooms[room].bridges:
                for chan in self.dialer.rooms[room].bridges[bridge].chans:
                    chans.append(chan.chan_id)
        return {"chans": chans}
