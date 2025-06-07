from pilgrim.service.mocks.entry_service_mock import EntryServiceMock
from pilgrim.service.mocks.photo_service_mock import PhotoServiceMock
from pilgrim.service.mocks.travel_diary_service_mock import TravelDiaryServiceMock
from pilgrim.service.photo_service import PhotoService
from pilgrim.service.servicemanager import ServiceManager


class ServiceManagerMock(ServiceManager):
    def __init__(self):
        super().__init__()

    def get_entry_service(self):
        return EntryServiceMock()

    def get_travel_diary_service(self):
        return TravelDiaryServiceMock()

    def get_photo_service(self):
        return PhotoServiceMock()