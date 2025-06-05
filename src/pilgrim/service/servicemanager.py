from pilgrim.service.entry_service import EntryService
from pilgrim.service.travel_diary_service import TravelDiaryService


class ServiceManager:
    def __init__(self):
        self.session = None
    def set_session(self, session):
        self.session = session
    def get_session(self):
        return self.session
    def get_entry_service(self):
        if self.session is not None:
            return EntryService(self.session)
        return None
    def get_travel_diary_service(self):
        if self.session is not None:
            return TravelDiaryService(self.session)
        return None