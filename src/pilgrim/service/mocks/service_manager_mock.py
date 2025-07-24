from pilgrim.service.mocks.entry_service_mock import EntryServiceMock
from pilgrim.service.mocks.photo_service_mock import PhotoServiceMock
from pilgrim.service.mocks.travel_diary_service_mock import TravelDiaryServiceMock
from pilgrim.service.servicemanager import ServiceManager


class ServiceManagerMock(ServiceManager):
    def __init__(self):
        super().__init__()
        # Cria instâncias únicas para manter estado consistente
        self._travel_diary_service = TravelDiaryServiceMock()
        self._entry_service = EntryServiceMock()
        self._photo_service = PhotoServiceMock()

    def get_entry_service(self):
        return self._entry_service

    def get_travel_diary_service(self):
        return self._travel_diary_service

    def get_photo_service(self):
        return self._photo_service