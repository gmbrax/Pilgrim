from unittest.mock import patch, MagicMock
from pilgrim.application import Application

@patch('pilgrim.application.UIApp')
@patch('pilgrim.application.ServiceManager')
@patch('pilgrim.application.Database')
@patch('pilgrim.application.ConfigManager')
def test_application_initialization_wires_dependencies(
    MockConfigManager, MockDatabase, MockServiceManager, MockUIApp
):
    mock_config_instance = MockConfigManager.return_value
    mock_db_instance = MockDatabase.return_value
    mock_session_instance = mock_db_instance.session.return_value
    mock_service_manager_instance = MockServiceManager.return_value
    app = Application()
    MockConfigManager.assert_called_once()
    MockDatabase.assert_called_once_with(mock_config_instance)
    MockServiceManager.assert_called_once()
    MockUIApp.assert_called_once_with(mock_service_manager_instance, mock_config_instance)
    mock_config_instance.read_config.assert_called_once()
    mock_db_instance.session.assert_called_once()
    mock_service_manager_instance.set_session.assert_called_once_with(mock_session_instance)

@patch('pilgrim.application.UIApp')
@patch('pilgrim.application.ServiceManager')
@patch('pilgrim.application.Database')
@patch('pilgrim.application.ConfigManager')
def test_application_run_calls_methods(
    MockConfigManager, MockDatabase, MockServiceManager, MockUIApp
):
    app = Application()
    mock_db_instance = app.database
    mock_ui_instance = app.ui
    app.run()
    mock_db_instance.create.assert_called_once()
    mock_ui_instance.run.assert_called_once()

@patch('pilgrim.application.UIApp')
@patch('pilgrim.application.ServiceManager')
@patch('pilgrim.application.Database')
@patch('pilgrim.application.ConfigManager')
def test_get_service_manager_creates_and_configures_new_instance(
    MockConfigManager, MockDatabase, MockServiceManager, MockUIApp
):
    app = Application()
    mock_db_instance = app.database
    fake_session = MagicMock()
    mock_db_instance.session.return_value = fake_session
    mock_db_instance.reset_mock()
    MockServiceManager.reset_mock()
    returned_manager = app.get_service_manager()
    mock_db_instance.session.assert_called_once()
    MockServiceManager.assert_called_once()
    returned_manager.set_session.assert_called_once_with(fake_session)

    assert returned_manager is MockServiceManager.return_value