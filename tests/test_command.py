from unittest.mock import patch
from pilgrim.command import main

@patch('pilgrim.command.Application')
def test_main_function_runs_application(MockApplication):
    mock_app_instance = MockApplication.return_value
    main()
    MockApplication.assert_called_once()
    mock_app_instance.run.assert_called_once()
