from loguru import logger

from src.config import Config
from src.http_clients.base_client import BaseClient


class MediaSonicClient(BaseClient):
    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self.log = logger.bind(object_id=f'{self.__class__.__name__}#{self.api_url}')
        self.log.info("Start PySonicClient")

    @property
    def api_url(self):
        return f'{self.config.pysonic_host}:{self.config.pysonic_port}'
