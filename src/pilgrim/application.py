from pilgrim.database import Database
from pilgrim.service.mocks.service_manager_mock import ServiceManagerMock
from pilgrim.service.servicemanager import ServiceManager
from pilgrim.ui.ui import UIApp


class Application:
    def __init__(self):
        self.database = Database()
        session = self.database.session()
        session_manager = ServiceManager()
        session_manager.set_session(session)
        self.ui = UIApp(session_manager)

    def run(self):
        self.database.create()
        self.ui.run()

    def get_service_manager(self):
        session = self.database.session()
        session_manager = ServiceManager()
        session_manager.set_session(session)
        return session_manager
