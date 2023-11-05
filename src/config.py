import json
import os


class Config(object):
    """Config for our app"""

    default = {
        "app": "callpy",
        "app_api_host": "127.0.0.1",
        "app_api_port": 8005,
        "alive": True,
        "shutdown": False,
        "log_console": True,
        "asterisk_host": "127.0.0.1",
        "asterisk_port": 8088,
        "asterisk_login": "asterisk",
        "asterisk_password": "asterisk",
        "pysonic_host": "127.0.0.1",
        "pysonic_port": 7005
    }

    def __init__(self, config_path: str = ''):
        """
        Create new config

        @param config_path: File path with configs
        @return None.
        """
        join_config = {}
        if config_path and os.path.isfile(config_path):
            with open(config_path, "r") as jsonfile:
                join_config = json.load(jsonfile)
        else:
            print('WARNING! Config path not found => The default configuration will be used')

        self.join_config: dict = join_config

        self.new_config = self.default.copy()
        self.new_config.update(join_config)
        self.alive: bool = bool(self.new_config['alive'])  # if true then start kill FastAPI and APP
        self.shutdown: bool = bool(self.new_config['shutdown'])  # if true then waiting for finish all tasks
        self.log_console: int = bool(self.new_config['log_console'])  # enable/disable log in console

        self.app: str = str(self.new_config['app'])
        self.app_api_host: str = str(self.new_config['app_api_host'])
        self.app_api_port: int = int(self.new_config['app_api_port'])
        self.asterisk_host: str = str(self.new_config['asterisk_host'])
        self.asterisk_port: int = int(self.new_config['asterisk_port'])
        self.asterisk_login: str = str(self.new_config['asterisk_login'])
        self.asterisk_password: str = str(self.new_config['asterisk_password'])

        self.pysonic_host: str = str(self.new_config['pysonic_host'])
        self.pysonic_port: int = int(self.new_config['pysonic_port'])

    def get_different_type_variables(self) -> list:
        different: list[str] = []
        for variable in self.new_config:
            new_type = type(self.default[variable])
            if variable not in self.default:
                different.append(f'not found config variable with name: {variable}')
            elif isinstance(self.new_config[variable], type(self.default[variable])) is False:
                different.append(f'{variable}: wrong={new_type}, right={type(self.new_config[variable])}')
        return different


if __name__ == "__main__":
    c = Config()
    print(c.alive)
