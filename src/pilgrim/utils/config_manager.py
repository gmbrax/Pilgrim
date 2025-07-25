import os.path
from threading import Lock

import tomli
import tomli_w

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
        self.config_dir = DirectoryManager.get_config_directory()
        self.__data = None

    def read_config(self):
        if os.path.exists(f"{DirectoryManager.get_config_directory()}/config.toml"):
            try:
                with open(f"{DirectoryManager.get_config_directory()}/config.toml", "rb") as f:
                    data = tomli.load(f)

            except tomli.TOMLDecodeError as e:
                raise ValueError(f"Invalid TOML configuration: {e}")
            except Exception as e:
                raise RuntimeError(f"Error reading configuration: {e}")

            self.__data = data
            self.database_url = self.__data["database"]["url"]
            self.database_type = self.__data["database"]["type"]

            if self.__data["settings"]["diary"]["auto_open_diary_on_startup"] == "":
                self.auto_open_diary = None
            else:
                self.auto_open_diary = self.__data["settings"]["diary"]["auto_open_diary_on_startup"]
            self.auto_open_new_diary = self.__data["settings"]["diary"]["auto_open_on_creation"]
        else:
            print("Error: config.toml not found.")
            self.create_config()
            self.read_config()

    def create_config(self, config: dict = None):
        # Garantir que o diretório de configuração existe
        config_dir = DirectoryManager.get_config_directory()
        if not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)

        default = {
            "database": {
                "url": f"{config_dir}/database.db",
                "type": "sqlite"
            },
            "settings": {
                "diary": {
                    "auto_open_diary_on_startup": "",
                    "auto_open_on_creation": False
                }
            }
        }
        if config is None:
            config = default

        try:
            with open(f"{config_dir}/config.toml", "wb") as f:
                tomli_w.dump(config, f)
        except Exception as e:
            raise RuntimeError(f"Error creating configuration: {e}")

    def save_config(self):
        if self.__data is None:
            self.read_config()
        if self.__data is None:
            raise RuntimeError("Error reading configuration.")

        self.__data["database"]["url"] = self.database_url
        self.__data["database"]["type"] = self.database_type
        self.__data["settings"]["diary"]["auto_open_diary_on_startup"] = self.auto_open_diary or ""
        self.__data["settings"]["diary"]["auto_open_on_creation"] = self.auto_open_new_diary
        try:
            self.create_config(self.__data)
        except Exception as e:
            raise RuntimeError(f"Error saving configuration: {e}")

    def set_config_dir(self, value):
        self.config_dir = value

    def set_database_url(self, value: str):
        self.database_url = value

    def set_auto_open_diary(self, value: str):
        self.auto_open_diary = value

    def get_auto_open_diary(self):
        return self.auto_open_diary

    def set_auto_open_new_diary(self, value: bool):
        self.auto_open_new_diary = value
