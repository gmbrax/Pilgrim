from pilgrim.database import Database
from pilgrim.service.servicemanager import ServiceManager
from pilgrim.ui.ui import UIApp
from pilgrim.utils import DirectoryManager, ConfigManager


class Application:
    def __init__(self):
        self.config_dir = DirectoryManager.get_config_directory()
        self.database = Database()
        self.config_manager = ConfigManager()
        session = self.database.session()
        session_manager = ServiceManager()
        session_manager.set_session(session)
        self.ui = UIApp(session_manager,self.config_manager)

    def run(self):
        self.database.create()
        self.ui.run()

    def get_service_manager(self):
        session = self.database.session()
        session_manager = ServiceManager()
        session_manager.set_session(session)
        return session_manager
