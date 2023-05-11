class Config(object):
    """Config for our app"""

    default = {'alive': True,
               'asterisk_host': '127.0.0.1',
               'asterisk_port': '8088',
               'asterisk_login': 'asterisk',
               'asterisk_password': 'asterisk'}

    def __init__(self, join_config: dict):
        self.join_config: dict = join_config

        self.new_config = self.default
        self.new_config.update(join_config)
        self.alive: bool = bool(self.new_config['alive'])
        self.asterisk_host: str = str(self.new_config['asterisk_host'])
        self.asterisk_port: int = int(self.new_config['asterisk_port'])
        self.asterisk_login: str = str(self.new_config['asterisk_login'])
        self.asterisk_password: str = str(self.new_config['asterisk_password'])


if __name__ == "__main__":
    c = Config(join_config={})
    print(c.alive)
