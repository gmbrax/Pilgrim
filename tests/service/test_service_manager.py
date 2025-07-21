from pilgrim.service.servicemanager import ServiceManager
from unittest.mock import patch, MagicMock

def test_initial_state_is_none():
    manager = ServiceManager()
    assert manager.get_session() is None
    assert manager.get_entry_service() is None
    assert manager.get_photo_service() is None
    assert manager.get_travel_diary_service() is None

@patch('pilgrim.service.servicemanager.TravelDiaryService')
@patch('pilgrim.service.servicemanager.PhotoService')
@patch('pilgrim.service.servicemanager.EntryService')
def test_get_services_instantiates_with_correct_session(
    mock_entry_service, mock_photo_service, mock_travel_diary_service
):
    manager = ServiceManager()
    mock_session = MagicMock()
    manager.set_session(mock_session)

    entry_service_instance = manager.get_entry_service()
    photo_service_instance = manager.get_photo_service()
    travel_diary_service_instance = manager.get_travel_diary_service()

    mock_entry_service.assert_called_once()
    mock_photo_service.assert_called_once()
    mock_travel_diary_service.assert_called_once()
    mock_entry_service.assert_called_once_with(mock_session)
    mock_photo_service.assert_called_once_with(mock_session)
    mock_travel_diary_service.assert_called_once_with(mock_session)
    assert entry_service_instance == mock_entry_service.return_value
    assert photo_service_instance == mock_photo_service.return_value
    assert travel_diary_service_instance == mock_travel_diary_service.return_value