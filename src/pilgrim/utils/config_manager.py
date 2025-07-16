from threading import Lock

import tomli
from pilgrim.utils import DirectoryManager

class SingletonMeta(type):
    _instances = {}
    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]

class ConfigManager(metaclass=SingletonMeta):
    def __init__(self):
        self.database_url = None
        self.database_type = None
        self.auto_open_diary = None
        self.auto_open_new_diary = None
    @staticmethod
    def read_config():
        try:
            with open(f"{DirectoryManager.get_config_directory()}/config.toml", "rb") as f:
                data = tomli.load(f)
            print(data)
        except FileNotFoundError:
            print("Error: config.toml not found.")
        except tomli.TOMLDecodeError as e:
            print(f"Error decoding TOML: {e}")

    def set_database_url(self):
        pass