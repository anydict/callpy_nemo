import json


class Config(object):
    default = {'alive': True,
               'asterisk_host': '127.0.0.1',
               'asterisk_port': '8088',
               'asterisk_login': 'asterisk',
               'asterisk_password': 'asterisk'}

    def __init__(self, path_config: str = '', dict_config=None):
        self.new_config = self.default
        if path_config != '':
            with open(path_config, "r") as jsonfile:
                self.new_config.update(json.load(jsonfile))

        if isinstance(dict_config, dict):
            self.new_config.update(dict_config)

        self.alive: bool = bool(self.new_config['alive'])
        self.asterisk_host: str = str(self.new_config['asterisk_host'])
        self.asterisk_port: int = int(self.new_config['asterisk_port'])
        self.asterisk_login: str = str(self.new_config['asterisk_login'])
        self.asterisk_password: str = str(self.new_config['asterisk_password'])


if __name__ == "__main__":
    c = Config()
    print(c.alive)
