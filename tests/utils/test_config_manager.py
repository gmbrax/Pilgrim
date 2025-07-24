import pytest
import tomli
from pathlib import Path
from unittest.mock import patch

from pilgrim.utils.config_manager import ConfigManager, SingletonMeta

@pytest.fixture
def clean_singleton():
    SingletonMeta._instances = {}

@patch('pilgrim.utils.config_manager.DirectoryManager.get_config_directory')
def test_create_default_config_if_not_exists_with_decorator(mock_get_config_dir, tmp_path: Path, clean_singleton):
    mock_get_config_dir.return_value = str(tmp_path)
    manager = ConfigManager()
    config_file = tmp_path / "config.toml"
    assert not config_file.exists()
    manager.read_config()
    assert config_file.exists()
    assert manager.database_type == "sqlite"

@patch('pilgrim.utils.config_manager.DirectoryManager.get_config_directory')
def test_read_existing_config_with_decorator(mock_get_config_dir, tmp_path: Path, clean_singleton):
    mock_get_config_dir.return_value = str(tmp_path)
    custom_config_content = """
    [database]
    url = "/custom/path/to/db.sqlite"
    type = "custom_sqlite"
    [settings.diary]
    auto_open_diary_on_startup = "MyCustomDiary"
    auto_open_on_creation = true
    """
    config_file = tmp_path / "config.toml"
    config_file.write_text(custom_config_content)

    manager = ConfigManager()
    manager.read_config()
    assert manager.database_url == "/custom/path/to/db.sqlite"
    assert manager.database_type == "custom_sqlite"

@patch('pilgrim.utils.config_manager.DirectoryManager.get_config_directory')
def test_save_config_writes_changes_to_file_with_decorator(mock_get_config_dir, tmp_path: Path, clean_singleton):
    mock_get_config_dir.return_value = str(tmp_path)
    manager = ConfigManager()
    manager.read_config()
    manager.set_database_url("/novo/caminho.db")
    manager.set_auto_open_new_diary(True)
    manager.save_config()
    config_file = tmp_path / "config.toml"
    with open(config_file, "rb") as f:
        data = tomli.load(f)
        assert data["database"]["url"] == "/novo/caminho.db"
        assert data["settings"]["diary"]["auto_open_on_creation"] is True

@patch('pilgrim.utils.config_manager.DirectoryManager.get_config_directory')
def test_read_config_raises_error_on_malformed_toml(mock_get_config_dir, tmp_path: Path, clean_singleton):
    mock_get_config_dir.return_value = str(tmp_path)
    invalid_toml_content = """
       [database]
       url = /caminho/sem/aspas
       """
    config_file = tmp_path / "config.toml"
    config_file.write_text(invalid_toml_content)
    manager = ConfigManager()
    with pytest.raises(ValueError, match="Invalid TOML configuration"):
        manager.read_config()