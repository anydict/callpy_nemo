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
        self.router.add_api_route("/", self.root, methods=["GET"])
        self.router.add_api_route("/diag", self.diag, methods=["GET"])
        self.router.add_api_route("/stats", self.stats, methods=["GET"])

    def root(self):
        return {"app": "callpy", "server": self.config.asterisk_host}

    def diag(self):
        return {"res": "OK", "alive": self.config.alive}

    def stats(self):
        return {"stats": "123", "alive": self.config.alive}
