from src.database import Database
from src.service.servicemanager import ServiceManager


class Application:
    def __init__(self):
        self.database = Database()

    def run(self):
        self.database.create()

    def get_service_manager(self):
        session = self.database.session()
        session_manager = ServiceManager()
        session_manager.set_session(session)
        return session_manager
