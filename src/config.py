import json


class Config(object):
    config = {'asterisk_host': '127.0.0.1',
              'asterisk_port': '8088',
              'asterisk_login': 'asterisk',
              'asterisk_password': 'asterisk'}

    def __init__(self, path_config: str, ):
        with open(path_config, "r") as jsonfile:
            new_config = json.load(jsonfile)
            self.config.update(new_config)
