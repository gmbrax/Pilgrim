from pilgrim.database import Database
from pilgrim.service.servicemanager import ServiceManager
from pilgrim.ui.ui import UIApp
from pilgrim.utils import ConfigManager


class Application:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.database = Database(self.config_manager)
        session = self.database.session()
        session_manager = ServiceManager()
        session_manager.set_session(session)
        self.ui = UIApp(session_manager,self.config_manager)

    def run(self):
        self.config_manager.read_config()
        self.database.create()
        self.ui.run()

    def get_service_manager(self):
        session = self.database.session()
        session_manager = ServiceManager()
        session_manager.set_session(session)
        return session_manager
